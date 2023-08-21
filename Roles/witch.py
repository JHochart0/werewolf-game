from Roles.role import Role

'''
Class Witch that gives information about the role "Witch", it inherits from the class "Role".
It has two attribute :
-"hasHealingPotion" to give if the healing potion was used or not.
-"hasPoisonPotion" to give if the poison potion was used or not.
'''
class Witch(Role):
	def __init__(self, name):
		super().__init__(name)
		self.hasHealingPotion = True
		self.hasPoisonPotion = True
		self.poisonedPlayer = ""
		self.strRole = "Witch"