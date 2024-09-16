

class Tool:
    def __init__(self, name, categotyId, isAlwaysOn, description, tier, value):
        self.name = name
        self.categotyId = categotyId
        self.isAlwaysOn = isAlwaysOn
        self.description = description
        self.tier = tier
        self.value = value
    
    def __str__(self):
        return "{}\n=====\n{}\nTier: {}\nValue: {}\n".format(self.name, self.description, self.tier, self.value)
