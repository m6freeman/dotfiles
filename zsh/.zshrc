#!/bin/sh

source /usr/share/fzf/completion.zsh
source /usr/share/fzf/key-bindings.zsh
source /usr/share/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh
source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# bind UP and DOWN arrow keys to history substring search
zmodload zsh/terminfo

source "$ZDOTDIR/src/variables"
source "$ZDOTDIR/src/key_bindings"
source "$ZDOTDIR/src/aliases"
source "$ZDOTDIR/src/functions"
source "$ZDOTDIR/src/prompt"

## Options section
setopt appendhistory                                            # Immediately append history instead of overwriting
setopt autocd                                                   # if only directory path is entered, cd there.
setopt correct                                                  # Auto correct mistakes
setopt extendedglob                                             # Extended globbing. Allows using regular expressions with *
setopt histignorealldups                                        # If a new command is a duplicate, remove the older one
setopt nobeep                                                   # No beep
setopt nocaseglob                                               # Case insensitive globbing
setopt nocheckjobs                                              # Don't warn about running processes when exiting
setopt numericglobsort                                          # Sort filenames numerically when it makes sense
setopt rcexpandparam                                            # Array expension with parameters
setopt nolistambiguous

autoload -Uz compinit && compinit -d $HOME/.local/share/zsh
zstyle ':completion:*' accept-exact '*(N)'
zstyle ':completion:*' cache-path ~/.zsh/cache
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"         # Colored completion (different colors for dirs/files/etc)
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'       # Case insensitive tab completion
zstyle ':completion:*' rehash true                              # automatically find new executables in path 
zstyle ':completion:*' use-cache on


# Print a greeting message when shell is started
wttr knoxville | head -n 7 | tail -n 5 ;
echo 'BTC:' $(curl -s http://api.coindesk.com/v1/bpi/currentprice.json | python -c "import json, sys; print('$' + json.load(sys.stdin)['bpi']['USD']['rate'].rsplit('.')[0])")
