import log_analyzer
import re
import unittest
import sys


def read_body(filename):
	log_file = open(filename, "r") #opens the text_file
	battle = log_analyzer.Battle() 
	start = [] #the lines associated before the first turn
	middle = []	#lines associated with each turn
	end = [] #lines associated after the battle is over
	turnsStarted = False
	battleOver = False
	for line in log_file: #splits the lines into start, middle, end
		if not turnsStarted:
			if  "Go!" not in line:
		   		start.append(line)
		   		continue
			else:
		   		turnsStarted = True
		if not battleOver:
			if "won" not in line and "lost due to inactivity" not in line and "forfeited" not in line:
				middle.append(line)
				continue
			else:
				battleOver = True
		else:
			end.append(line)
	analyze_start(start, battle)
	# print(middle)
	string_turns = split_turns(middle)
	for turn in string_turns:
		analyze_turn(turn, string_turns[turn], battle)
	analyze_end(end[0], battle)

	log_file.close()
	return battle

def analyze_start(start, battle):
	numOfPlayers = 0
	format = False
	player1Team = False
	player2Team = False
	for line in start:

		line = line.rstrip('\n')

		matchPlayer = re.match( r'(.*) joined.', line)
		
		if matchPlayer and numOfPlayers < 2:
			if numOfPlayers == 0:
				player1 = log_analyzer.Player(matchPlayer.group(1), 1)
			else:
				player2 = log_analyzer.Player(matchPlayer.group(1), 2)
				battle.add_players(player1, player2)
			numOfPlayers = numOfPlayers + 1
		
		elif "Format:" in line:
			format = True
		elif format:
			battle.define_battle(line)
			format = False
		elif "rated Battle" in line:
			battle.rated = True
		elif "Clause:" in line or "Mod:" in line:
			battle.conditions.append(line)
		elif battle.player1 and battle.player1.name + "'s team" in line:
			player1Team = True
		elif player1Team:
			team = line.split(" / ")
			for pokemon in team:
				pokemon_object = log_analyzer.Pokemon(pokemon, player1)
				battle.player1.team.append(pokemon_object)
			player1Team = False
		elif battle.player2 and battle.player2.name + "'s team" in line:
			player2Team = True
		elif player2Team:
			team = line.split(" / ")
			for pokemon in team:
				pokemon_object = log_analyzer.Pokemon(pokemon, player2)
				battle.player2.team.append(pokemon_object)
			player2Team = False

		
		

def split_turns(middle): 
	#returns a dictionary of number to Turn, starting at 0
	turn_num = 0
	new_turn = ""
	string_turns = {}
	for line in middle:
		if "Turn" not in line:
			new_turn += line
		else:
			string_turns[turn_num] = new_turn
			new_turn = ""
			turn_num += 1
	string_turns[turn_num] = new_turn
	return string_turns

def analyze_turn(number, turn, battle):
	this_turn = log_analyzer.Turn(number)
	battle.all_turns.append(this_turn)
	battle.turn_number = number
	if number != 0:
		for pokemon in battle.all_turns[number - 1].p1_pokemon:
			this_turn.p1_pokemon.append(pokemon.copy(this_turn)) #should deep copy pokemon from previous turn
		for pokemon in battle.all_turns[number - 1].p2_pokemon:
			this_turn.p2_pokemon.append(pokemon.copy(this_turn))
	else: #for turn 0
		for pokemon in battle.player1.team:
			this_turn.p1_pokemon.append(pokemon.copy(this_turn))
		for pokemon in battle.player2.team:
			this_turn.p2_pokemon.append(pokemon.copy(this_turn))
	match_p1_send_out = re.finditer( r'Go! (.*)!', turn) #This is turn0
	match_p2_send_out = re.finditer( r'(.*) sent out (.*)!', turn)
	match_mega = re.finditer( r'(.*) has Mega Evolved into Mega (.*)!', turn)
	match_attack = re.finditer( r'((.*) used (.*)!)(\n(.*)!)*', turn) #matches the attack and all the consequences
	match_pokemon_fainted = re.finditer(r'(.*) fainted', turn)
	match_p1_withdraw = re.finditer(r'(.*), come back!', turn)
	match_p2_withdraw = re.finditer( r'(.*) withdrew (.*)!', turn)
	for match in match_p1_send_out:
		for pokemon in this_turn.p1_pokemon:
			if pokemon.name == match.group(1):
				pokemon.in_play = True
				break
	for match in match_p2_send_out:
		for pokemon in this_turn.p2_pokemon:
			if pokemon.name == match.group(2):
				pokemon.in_play = True
				break
	for match in match_mega:
		match_mega_pokemon = match.group(2)
		for pokemon in this_turn.p1_pokemon + this_turn.p2_pokemon:
			if pokemon.name == match_mega_pokemon:
				pokemon.mega_evolved = True
				break
	for match in match_attack:
		entire_attack = match.group(1)
		pokemon_name = match.group(2)
		attack = match.group(3)
		consequences = match.group(4).strip()
		this_turn.actions[entire_attack] = consequences
		if "opposing" in pokemon_name:
			for pokemon in this_turn.p2_pokemon:
				if "The opposing " + pokemon.name == pokemon_name:
					pokemon.actions[attack] = consequences
					battle.player2.actions[entire_attack] = consequences
					break
		else:
			for pokemon in this_turn.p1_pokemon:
				if pokemon.name == pokemon_name:
					pokemon.actions[attack] = consequences
					battle.player1.actions[entire_attack] = consequences
					break
	for match in match_pokemon_fainted:
		fainted_pokemon = match.group(1)
		if "opposing" in fainted_pokemon:
			for pokemon in this_turn.p2_pokemon:
				if "The opposing" + pokemon.name == fainted_pokemon:
					pokemon.faint(this_turn)
					break
		else:
			for pokemon in this_turn.p1_pokemon:
				if pokemon.name == fainted_pokemon:
					pokemon.faint(this_turn)
					break
	for match in match_p1_withdraw:
		battle.player1.actions[match.group(0)] = None
		pokemon_name = match.group(1)
		for pokemon in [this_turn.p1_pokemon] + [this_turn.p2.pokemon]:
			if pokemon.name == pokemon_name:
				pokemon.in_play = False


#withdraw and

#player's actions each turn
# 1. trainer can have a pokemon attack
# 2. trainer can swap out a pokemon for another
# if the 

#


def analyze_end(end, battle):
	for line in end:
		pass

class Test(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.battle = read_body('Example_Battle_Format.txt')

	def test_both_players(self):
		self.assertEqual(self.battle.player1.name, "redfor")
		self.assertEqual(self.battle.player2.name, "BOON305")
	def test_pokemon_team(self):

		self.assertEqual((len(self.battle.player1.team)), 6)
		self.assertEqual(self.battle.player2.team[1].name, "Charizard")
		self.assertEqual(self.battle.player2.team[5].name, "Clefairy")
		self.assertEqual(self.battle.player1.team[5].name, "Gourgeist-*")
	def test_clauses(self):
		self.assertTrue(self.battle.conditions)
	def test_mega(self):
		self.assertTrue(self.battle.all_turns[1].p1_pokemon[4].mega_evolved) #make sure Kanghaskan mega_evolved
		self.assertTrue(self.battle.all_turns[2].p1_pokemon[4].mega_evolved)
		self.assertFalse(self.battle.all_turns[0].p1_pokemon[4].mega_evolved)
	def test_actions(self):
		# print(self.battle.player2.start_team[1].actions)
		self.assertEqual(self.battle.player2.actions["The opposing Meowstic used Quick Guard!"], "Quick Guard protected the opposing team!")
		self.assertEqual(self.battle.player1.actions["Kangaskhan used Fake Out!"], "Quick Guard protected the opposing Meowstic!")
		# self.assertEqual(self.battle.player2.start_team[1].actions)
		#need to fix multiple consequences to one action
		#need to fix multiples of the same actin by the same move and not replacing from a previous turn
	def test_fainted(self):
		pass


# read_body('Example_Battle_Format.txt')

	# def testError(self):
	# 	raise RuntimeError('Test error!')

if __name__ == "__main__":
	# battle = read_body(sys.argv[1])
	# battle = read_body('Example_Battle_Format')
	unittest.main()



#divide into description, intro, turns, after_battle
#return a Dictionary?
#.... joined
#___________
#Battle between _____ and ____ started!
#___________
#Turn 1
#___________
# redfor lost due to inactivity.
# or 
# BOON305 won the battle!