# -*- coding: utf-8 -*-
from nemesis.app import app
from nemesis.lib.utils import safe_dict


def make_file_url(fmeta):
    devourer_url = app.config['DEVOURER_URL'].rstrip('/') + '/'
    if fmeta.uuid:
        return u'{0}{1}'.format(
            devourer_url,
            u'api/0/download/{0}'.format(fmeta.uuid.hex)
        )


def represent_file_meta(fmeta):
    return {
        'id': fmeta.id,
        'name': fmeta.name,
        'mimetype': fmeta.mimetype,
        'note': fmeta.note,
        'url': make_file_url(fmeta)
    }


def represent_action_file(action_attach):
    res = safe_dict(action_attach)
    res.update({
        'file_meta': represent_file_meta(action_attach.file_meta)
    })
    return res
