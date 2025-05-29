from flask import Flask, render_template, request, jsonify, session
import json
import re
from collections import defaultdict, deque
import heapq
from typing import List, Dict, Tuple, Optional, Set
from translations import TRANSLATIONS

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session

class BusRouteFinder:
    def __init__(self):
        self.graph = defaultdict(list)  # adjacency list
        self.bus_routes = {}  # bus_name -> list of stops
        self.stop_to_buses = defaultdict(set)  # stop -> set of buses
        self.all_stops = set()
        
    def load_data(self, bus_data_file: str, places_file: str):
        """Load bus data and places from files"""
        # Load bus data
        with open(bus_data_file, 'r', encoding='utf-8') as f:
            bus_data = json.load(f)
        
        # Load places from places.js
        with open('static/places.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Extract the array from the JavaScript content
        # Assuming the format is 'var places = [...];'
        match = re.search(r'var places = (.*?);', js_content, re.DOTALL)
        if match:
            places_array_str = match.group(1)
            # Safely evaluate the string as a Python literal (list)
            places = json.loads(places_array_str)
        else:
            places = [] # Fallback to empty list if parsing fails
        
        self.all_stops = set(places)
        self._process_bus_routes(bus_data)
        
    def _extract_stops_from_route(self, route_string: str) -> List[str]:
        """Extract stop names from route string"""
        # Split by ⇄ and clean up each stop
        stops = []
        parts = route_string.split('⇄')
        
        for part in parts:
            part = part.strip()
            if part:
                # Extract English name (before parentheses)
                match = re.match(r'^([^(]+)', part)
                if match:
                    stop_name = match.group(1).strip()
                    stops.append(stop_name)
        
        return stops
    
    def _process_bus_routes(self, bus_data: List[Dict]):
        """Process bus routes and build graph"""
        for bus_info in bus_data:
            bus_name = bus_info['Bus Name']
            route_string = bus_info['Route']
            
            stops = self._extract_stops_from_route(route_string)
            self.bus_routes[bus_name] = stops
            
            # Add stops to graph and track which buses serve each stop
            for i, stop in enumerate(stops):
                self.stop_to_buses[stop].add(bus_name)
                
                # Connect adjacent stops in the route
                if i > 0:
                    prev_stop = stops[i-1]
                    # Bidirectional connection
                    self.graph[prev_stop].append((stop, bus_name, 1))  # (destination, bus, weight)
                    self.graph[stop].append((prev_stop, bus_name, 1))
    
    def find_direct_route(self, start: str, end: str) -> List[Dict]:
        """Find direct bus routes between two stops"""
        direct_routes = []
        start_buses = self.stop_to_buses.get(start, set())
        end_buses = self.stop_to_buses.get(end, set())
        
        common_buses = start_buses.intersection(end_buses)
        
        for bus_name in common_buses:
            route = self.bus_routes[bus_name]
            try:
                start_idx = route.index(start)
                end_idx = route.index(end)
                
                if start_idx != end_idx:
                    # Extract the path between start and end
                    if start_idx < end_idx:
                        path = route[start_idx:end_idx + 1]
                    else:
                        path = route[end_idx:start_idx + 1]
                        path.reverse()
                    
                    direct_routes.append({
                        'bus_name': bus_name,
                        'path': path,
                        'stops_count': len(path) - 1
                    })
            except ValueError:
                continue
        
        return sorted(direct_routes, key=lambda x: x['stops_count'])
    
    def find_route_with_preference(self, start: str, end: str, preference: str = 'fastest') -> Optional[Dict]:
        """Find route based on user preference"""
        if start not in self.all_stops or end not in self.all_stops:
            return None
            
        if preference == 'fastest':
            return self.dijkstra_with_transfers(start, end, weight_type='time')
        elif preference == 'least_transfer':
            return self.dijkstra_with_transfers(start, end, weight_type='transfers')
        elif preference == 'shortest':
            return self.dijkstra_with_transfers(start, end, weight_type='distance')
        else:
            return self.dijkstra_with_transfers(start, end, weight_type='time')  # default to fastest

    def dijkstra_with_transfers(self, start: str, end: str, weight_type: str = 'time') -> Optional[Dict]:
        """Find shortest path with possible transfers using Dijkstra's algorithm"""
        if start not in self.all_stops or end not in self.all_stops:
            return None
        
        # Priority queue: (cost, current_stop, path, buses_used)
        pq = [(0, start, [start], [])]
        visited = set()
        
        while pq:
            cost, current, path, buses_used = heapq.heappop(pq)
            
            if current == end:
                return {
                    'path': path,
                    'buses_used': buses_used,
                    'total_cost': cost,
                    'transfers': len(buses_used) - 1 if buses_used else 0,
                    'preference': weight_type
                }
            
            if current in visited:
                continue
            
            visited.add(current)
            
            # Explore neighbors
            for next_stop, bus_name, weight in self.graph[current]:
                if next_stop not in visited:
                    new_cost = cost
                    new_path = path + [next_stop]
                    
                    # Calculate cost based on preference
                    if weight_type == 'time':
                        new_cost += weight  # Base weight for time
                        if buses_used and buses_used[-1] != bus_name:
                            new_cost += 5  # Transfer penalty in minutes
                    elif weight_type == 'transfers':
                        new_cost = len(buses_used)  # Count of transfers
                        if buses_used and buses_used[-1] != bus_name:
                            new_cost += 1  # Additional transfer
                    elif weight_type == 'distance':
                        new_cost += weight  # Base weight for distance
                        if buses_used and buses_used[-1] != bus_name:
                            new_cost += 2  # Small penalty for transfers
                    
                    # Check if we're continuing with the same bus or switching
                    if buses_used and buses_used[-1] == bus_name:
                        new_buses = buses_used[:]
                    else:
                        new_buses = buses_used + [bus_name]
                    
                    heapq.heappush(pq, (new_cost, next_stop, new_path, new_buses))
        
        return None
    
    def format_route_instructions(self, route_result: Dict) -> List[Dict]:
        """Format route result into clear instructions"""
        if not route_result:
            return []
        
        path = route_result['path']
        buses_used = route_result['buses_used']
        
        instructions = []
        current_bus = None
        segment_start = 0
        
        for i, stop in enumerate(path):
            # Find which bus to use for this segment
            if i < len(path) - 1:
                next_stop = path[i + 1]
                # Find bus that connects current stop to next stop
                for bus_name in self.stop_to_buses[stop]:
                    if bus_name in self.stop_to_buses[next_stop]:
                        if current_bus != bus_name:
                            # Bus change needed
                            if current_bus is not None:
                                # Complete previous segment
                                instructions.append({
                                    'type': 'ride',
                                    'bus': current_bus,
                                    'from': path[segment_start],
                                    'to': stop,
                                    'stops': path[segment_start:i+1]
                                })
                                
                                # Add transfer instruction
                                instructions.append({
                                    'type': 'transfer',
                                    'location': stop,
                                    'from_bus': current_bus,
                                    'to_bus': bus_name
                                })
                            
                            current_bus = bus_name
                            segment_start = i
                        break
        
        # Add final segment
        if current_bus:
            instructions.append({
                'type': 'ride',
                'bus': current_bus,
                'from': path[segment_start],
                'to': path[-1],
                'stops': path[segment_start:]
            })
        
        return instructions

# Initialize the route finder
route_finder = BusRouteFinder()

@app.route('/')
def index():
    """Render the main page"""
    # Set default language to English if not set
    if 'language' not in session:
        session['language'] = 'en'
    
    # Get the current language
    current_language = session.get('language', 'en')
    
    # Pass both translations and current language to template
    return render_template('index.html', 
                         translations=TRANSLATIONS[current_language],
                         session=session)

@app.route('/api/set-language', methods=['POST'])
def set_language():
    """Set the user's preferred language"""
    data = request.json
    language = data.get('language', 'en')
    
    if language not in TRANSLATIONS:
        return jsonify({'error': 'Unsupported language'}), 400
    
    # Update session language
    session['language'] = language
    
    # Return success with current language
    return jsonify({
        'success': True, 
        'language': language,
        'translations': TRANSLATIONS[language]
    })

@app.route('/api/places')
def get_places():
    """Get all available places for dropdown"""
    return jsonify(sorted(list(route_finder.all_stops)))

@app.route('/api/find-route', methods=['POST'])
def find_route():
    """Find route between two places"""
    data = request.json
    start = data.get('start')
    end = data.get('end')
    preference = data.get('preference', 'fastest')
    
    if not start or not end:
        return jsonify({'error': TRANSLATIONS[session['language']]['error']}), 400
    
    if start == end:
        return jsonify({'error': TRANSLATIONS[session['language']]['error']}), 400
    
    # Find direct routes first
    direct_routes = route_finder.find_direct_route(start, end)
    
    # Find routes with transfers based on preference
    transfer_route = route_finder.find_route_with_preference(start, end, preference)
    
    result = {
        'start': start,
        'end': end,
        'preference': preference,
        'direct_routes': direct_routes,
        'transfer_route': None,
        'instructions': []
    }
    
    if transfer_route:
        result['transfer_route'] = transfer_route
        result['instructions'] = route_finder.format_route_instructions(transfer_route)
    
    return jsonify(result)

if __name__ == '__main__':
    # Load data (you'll need to adjust these paths)
    try:
        route_finder.load_data('bus_data.json', 'places.txt')
        print(f"Loaded {len(route_finder.bus_routes)} bus routes")
        print(f"Loaded {len(route_finder.all_stops)} stops")
        app.run(debug=True, port=5000)
    except FileNotFoundError as e:
        print(f"Error loading data files: {e}")
        print("Please make sure 'bus_data.json' and 'places.txt' are in the same directory")
