"""Task management

For shell tab completions:
http://docs.pyinvoke.org/en/stable/invoke.html#shell-tab-completion
Examples for zsh shell:
source <(inv --print-completion-script zsh)
inv --print-completion-script zsh > ~/.invoke-completion.sh
"""

try:
    from ._collections import ns
    # TODO: see if tasks.dedupe helps with running a clean task both pre and post
    ns.configure(dict(run=dict(pty=True, echo=True), tasks=dict(dedupe=False)))
except ImportError:
    print("Invoke collections not imported due to import error.")
