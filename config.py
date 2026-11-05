import json

class Config:
    def __init__(self, path='database/config.json'):
        self.path = path
        self.config = None
        self.framework = {
            'user': '',
            'last_interaction_id': '',
            'summary': ''
        }

        self.summary = ''
        self.last_interaction_id = ''
        self.user = ''

        self.load()

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, value):
        self._user = value
        if not self.config is None:
            self.config['user'] = self._user
            self.save()

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, value):
        self._summary = value
        if not self.config is None:
            self.config['summary'] = self._summary
            self.save()

    @property
    def last_interaction_id(self):
        return self._last_interaction_id

    @last_interaction_id.setter
    def last_interaction_id(self, value):
        self._last_interaction_id = value
        if not self.config is None:
            self.config['last_interaction_id'] = self._last_interaction_id
            self.save()

    def save(self):
        try:
            with open(self.path, 'w') as fp:
                formatted_config = json.dumps(self.config)
                fp.writelines(formatted_config)
                fp.close()
        except TypeError:
            print('Oops, il y a une erreur dans le type des données de config')

    def load(self):
        try:
            with open(self.path, 'r') as fp:
                config = json.load(fp)
                fp.close()

                for key in self.framework.keys():
                    if not key in config.keys():
                        raise json.JSONDecodeError('Oops, votre fichier de configuration est corrompu')
                    self.config = config

        except json.JSONDecodeError:
            self.config = self.framework

        except FileNotFoundError:
            self.config = self.framework