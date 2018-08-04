from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from game.core.models.game_models import Player, Problem, Solution

class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.game_room_name = 'ipod_submarine'
        async_to_sync(self.channel_layer.group_add)(
            self.game_room_name,
            self.channel_name
        )
        self.accept()
    
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.game_room_name,
            self.channel_name
        )
    
    def receive(self, text_data):
        data = json.loads(text_data)
        self.map_command_to_function(data)
    
    def map_command_to_function(self, data):
        self.commands[data['command']](self, data)
    
    def send_message(self, message):
        self.send(text_data=json.dumps(message))

    # Game Commands
    def init_game(self, data):
        username = data['username']
        player, created = Player.objects.get_or_create(username=username)
        content = {
            'command': 'join_game'
        }
        if not username:
            content['error'] = 'Unable to get or create Player with username: ' + username
            self.send_message(content)
        content['success'] = 'Joined game as player: ' + username
        self.send_message(content)

    def fetch_players(self, data):
        players = Player.objects.all()
        content = {
            'command': 'fetch_players',
            'players': self.players_to_json(players) # Helpers
        }
        self.send_message(content)
    
    def new_solution(self, data):
        username = data['username']
        solution_text = data['solution']
        problem_text = data['problem']
        player, player_created = Player.objects.get_or_create(username=username)
        problem, problem_created = Problem.objects.get_or_create(text=problem_text)
        solution = Solution.objects.create(author=player, solution_text=solution_text, problem=problem)
        content = {
            'command': 'new_solution',
            'solution': solution_text
        }
        self.send_message(content)
    
    # Helpers
    def players_to_json(self, players):
        result = []
        for player in players:
            result.append({
                'username': str(player),
                'points': str(player.points)
            })
        return result
    
    commands = {
        'init_game': init_game,
        'fetch_players': fetch_players,
        'new_solution': new_solution,
    }