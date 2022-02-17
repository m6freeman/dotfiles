source $HOME/.config/nvim/general/settings.vim
source $HOME/.config/nvim/keys/mappings.vim
source $HOME/.config/nvim/vim-plug/plugins.vim
source $HOME/.config/nvim/languages/python.lua
source $HOME/.config/nvim/vim-plug/compe/compe-config.lua

if exists('+termguicolors')
    let &t_8f = "\<Esc>[38;2;%lu;%lum]"
    let &t_8b = "\<Esc>[48;2;%lu;%lum]"
endif
let g:gruvbox_invert_selection='0'
let g:airline_theme='base16_gruvbox_dark_hard'

colorscheme gruvbox

