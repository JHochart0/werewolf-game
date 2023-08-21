from Roles.role import Role

'''
Class Werewolf that gives information about the role "Werewolf", it inherits from the class "Role".
It has an attribute "personEatten" to give who was decided to be eatten during the night.
'''
class Werewolf(Role):
	def __init__(self, name):
		super().__init__(name)
		self.personEatten = ""
		self.strRole="Werewolf"