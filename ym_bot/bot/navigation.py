from ym_bot.services.state import StateManager
from ym_bot.ui.keyboards import KeyboardBuilder


class ListNavigationService:
    def __init__(self, ctx):
        self.ctx = ctx

    def restore_list_view(self, cid, mid):
        if cid not in StateManager.user_states or not StateManager.user_states[cid]:
            return
        state = StateManager.user_states[cid][-1]
        hb = len(StateManager.user_states[cid]) > 1
        kb = None
        if state['type'] == 'tracks':
            kb = KeyboardBuilder.create_paginated_download_keyboard(state['tracks'], state['page'], state.get('album_id'), state.get('playlist_info'), has_back=hb)
        elif state['type'] in ['albums', 'artist_albums']:
            kb = KeyboardBuilder.create_paginated_keyboard(state['items'], 'album', state['page'], get_text=lambda i: f"{i.title} ({getattr(i,'year','?')})", has_back=hb)
        elif state['type'] == 'artists':
            kb = KeyboardBuilder.create_paginated_keyboard(state['items'], 'artist', state['page'], get_text=lambda i: i.name, has_back=hb)
        elif state['type'] == 'playlists':
            kb = KeyboardBuilder.create_paginated_keyboard(state['items'], 'playlist', state['page'], get_text=lambda i: f"{i.title} - {i.owner.name if hasattr(i,'owner') else '?'}", has_back=hb)
        if kb:
            self.ctx.bot.edit_message_text(state['label'], cid, mid, reply_markup=kb, parse_mode='HTML')
