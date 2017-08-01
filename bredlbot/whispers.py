def w_mod_status(channel, is_mod):
    if is_mod:
        return "/w {} BredlBot is live and has mod status.".format(channel)
    else:
        return "/w {} BredlBot is live without mod status. \
        Type '/mod BredlBot' and then whisper '!mod'.".format(channel)