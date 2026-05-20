import click
import subprocess
import sys
import difflib

from core import get_installed_gui_apps, uninstall_packages


def perform_uninstall(query, full):
    apps = get_installed_gui_apps()
    if not apps:
        click.echo("No applications found on this system.")
        return

    grouped_apps = {}
    for path, name in apps.items():
        name_lower = name.lower()
        if name_lower not in grouped_apps:
            grouped_apps[name_lower] = (name, [])
        grouped_apps[name_lower][1].append(path)

    query_clean = query.lower().strip()

    exact_matches = []
    prefix_matches = []
    substring_matches = []

    for name_lower, (original_name, paths) in grouped_apps.items():
        if name_lower == query_clean:
            exact_matches.append(name_lower)
        elif name_lower.startswith(query_clean):
            prefix_matches.append(name_lower)
        elif query_clean in name_lower:
            substring_matches.append(name_lower)

    prefix_matches.sort(key=lambda x: (len(x), x))
    substring_matches.sort(key=lambda x: (len(x), x))

    matches = exact_matches + prefix_matches + substring_matches

    if not matches:
        fuzzy = difflib.get_close_matches(query_clean, list(grouped_apps.keys()), cutoff=0.3)
        matches = fuzzy

    seen = set()
    deduped_matches = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            deduped_matches.append(m)

    if not deduped_matches:
        click.echo(f"Could not find any application matching '{query}'.")
        return

    best_match_key = deduped_matches[0]
    best_match_name, best_match_paths = grouped_apps[best_match_key]

    if len(deduped_matches) == 1:
        click.echo(f"Found application: {best_match_name}")
        if click.confirm(f"Do you want to uninstall {best_match_name}?"):
            uninstall_packages(best_match_paths, full=full)
    else:
        other_matches_names = [grouped_apps[m][0] for m in deduped_matches[1:]]
        click.echo(f"Found best match: {best_match_name}")
        click.echo(f"Other matches found: {', '.join(other_matches_names)}")

        choice = click.prompt(
            f"Do you want to uninstall {best_match_name}? [y/n/l]\n(y: Yes, n: No/Cancel, l: List all matches to choose)",
            type=click.Choice(['y', 'n', 'l'], case_sensitive=False),
            default='y'
        )

        if choice.lower() == 'y':
            uninstall_packages(best_match_paths, full=full)
        elif choice.lower() == 'l':
            click.echo("\nMatching applications:")
            for idx, match_key in enumerate(deduped_matches, 1):
                click.echo(f"{idx}. {grouped_apps[match_key][0]}")

            val = click.prompt(
                f"Select an application (1-{len(deduped_matches)}) or 'q' to cancel",
                type=str,
                default='1'
            )
            if val.lower() == 'q':
                click.echo("Cancelled.")
                return
            try:
                selected_idx = int(val) - 1
                if 0 <= selected_idx < len(deduped_matches):
                    target_key = deduped_matches[selected_idx]
                    target_name, target_paths = grouped_apps[target_key]
                    if click.confirm(f"Uninstall {target_name}?"):
                        uninstall_packages(target_paths, full=full)
                else:
                    click.echo("Invalid selection.")
            except ValueError:
                click.echo("Invalid input.")
        else:
            click.echo("Cancelled.")


class AppUninstallGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = super().get_command(ctx, cmd_name)
        if rv is not None:
            return rv

        def custom_action(full=False):
            perform_uninstall(cmd_name, full)

        return click.Command(
            cmd_name,
            callback=custom_action,
            params=[click.Option(['--full'], is_flag=True, help="Remove all cache and config files")]
        )


def run_interactive_menu(ctx):
    ascii_art = """
 ██████╗███████╗ ██████╗ █████╗ ███████╗
██╔════╝██╔════╝██╔════╝██╔══██╗╚══███╔╝
╚█████╗ █████╗  ██║     ███████║  ███╔╝ 
 ╚═══██╗██╔══╝  ██║     ██╔══██║ ███╔╝  
██████╔╝███████╗╚██████╗██║  ██║███████╗
╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚══════╝
"""
    click.echo(click.style(ascii_art, fg='cyan', bold=True))
    click.echo(click.style("=== SECAZ: The Ultimate Linux App Uninstaller ===", fg='green', bold=True))
    click.echo()

    while True:
        click.echo("Please select an option:")
        click.echo(" 1) List all installed apps and tick/uninstall (Interactive FZF)")
        click.echo(" 2) Fuzzy-search & uninstall a specific app")
        click.echo(" 3) View standard CLI Help")
        click.echo(" 4) Exit")
        click.echo()

        choice = click.prompt("Enter choice (1-4)", type=str, default='1')

        if choice == '1':
            ctx.invoke(uninstall)
            break
        elif choice == '2':
            query = click.prompt("Enter application name to search")
            full_clean = click.confirm("Perform a deep clean (remove cache/configs too)?", default=False)
            perform_uninstall(query, full_clean)
            break
        elif choice == '3':
            click.echo(ctx.get_help())
            break
        elif choice == '4' or choice.lower() == 'q':
            click.echo("Goodbye!")
            ctx.exit()
        else:
            click.echo("Invalid option. Please choose 1, 2, 3, or 4.")
            click.echo()


@click.group(cls=AppUninstallGroup, invoke_without_command=True)
@click.option('-u', '--uninstall', 'uninstall_target', help="Uninstall a specific application")
@click.option('-f', '--full', is_flag=True, help="Remove all cache and config files")
@click.pass_context
def cli(ctx, uninstall_target, full):
    if uninstall_target:
        perform_uninstall(uninstall_target, full)
        ctx.exit()
    if ctx.invoked_subcommand is None:
        run_interactive_menu(ctx)


@cli.command()
@click.option('--full', is_flag=True, help="Remove all cache and config files")
def uninstall(full):
    apps = get_installed_gui_apps()
    if not apps:
        click.echo("No applications found.")
        return

    app_names_to_paths = {name: path for path, name in apps.items()}
    app_names = list(apps.values())
    app_names.sort()

    try:
        selected_names = fzf_multi_select(app_names, 'Select apps to uninstall (Tab to select multiple):')
        if not selected_names:
            return

        click.echo("Selected for uninstallation: " + ", ".join(selected_names))
        if click.confirm("Proceed with uninstallation?"):
            target_desktops = [app_names_to_paths[name] for name in selected_names]
            uninstall_packages(target_desktops, full=full)
    except ValueError as e:
        click.echo(str(e))


def fzf_multi_select(options, prompt_text):
    try:
        p = subprocess.Popen(['fzf', '-m', '--prompt', prompt_text + ' '], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        p.stdin.write('\n'.join(options).encode())
        p.stdin.close()
        selected = p.stdout.read().decode().strip().split('\n')
        selected = [s for s in selected if s]
        if not selected:
            raise ValueError('No selection made')
        return selected
    except FileNotFoundError:
        click.echo('fzf not found, falling back to manual selection')
        for i, opt in enumerate(options, 1):
            click.echo(f'{i}: {opt}')
        choices = click.prompt('Enter numbers separated by comma', type=str)
        selected = []
        for choice in choices.split(','):
            try:
                selected.append(options[int(choice.strip()) - 1])
            except (ValueError, IndexError):
                pass
        if not selected:
            raise ValueError('No selection made')
        return selected


if __name__ == '__main__':
    cli()
