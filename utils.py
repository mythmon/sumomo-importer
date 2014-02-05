import json


class Link(object):
    def __init__(self, *args):
        (self.kind, self.target, self.extra, self.slug, self.locale,
         self.hash) = args

    @property
    def args(self):
        return (self.kind, self.target, self.extra, self.slug, self.locale,
                self.hash)

    def __repr__(self):
        return ('<sumomomig.utils.Link (' +
                ', '.join(str(x) for x in self.args) +
                ')>')

    def __str__(self):
        linktext = self.target or ''
        if self.kind != 'Article':
            if not linktext.startswith(self.kind + ':'):
                linktext = self.kind + ':' + linktext
        if self.hash:
            linktext += self.hash
        if self.extra:
            linktext += '|' + self.extra
        return '[[' + linktext + ']]'

    def __json__(self):
        return self.args


class Image(object):

    def __init__(self, *args):
        (self.title, self.locale, self.description, self.file,
         self.thumbnail) = args

    @property
    def args(self):
        return (self.title, self.locale, self.description, self.file,
                self.thumbnail)

    def __repr__(self):
        return '<sumomomig.utils.Image "{0.title}">'.format(self)

    def __json__(self):
        return self.args

    def as_dict(self):
        return {
            'title': self.title,
            'locale': self.locale,
            'description': self.description,
            'file': self.file,
            'thumbnail': self.thumbnail,
        }


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)

        elif hasattr(obj, '__json__'):
            return obj.__json__()

        return super(MyEncoder, self).default(obj)


def write_out(data, step):
    with open(step + '.out.json', 'w') as f:
        json.dump(data, f, cls=MyEncoder, indent=4, sort_keys=True)


def read_in(from_step):
    with open(from_step + '.out.json') as f:
        data = json.load(f)
    data['links'] = [Link(*l) for l in data['links']]
    data['images'] = [Image(*l) for l in data['images']]
    for doc in data['docs']:
        doc['links'] = [Link(*l) for l in doc['links']]
    return data
