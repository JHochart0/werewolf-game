from Roles.role import Role

'''
Class Villager that gives information about the role "Villager", it inherits from the class "Role".
It has no particular attribute since it does nothing special.
'''
class Villager(Role):
	def __init__(self, name):
		super().__init__(name)
		self.strRole = "Villager"