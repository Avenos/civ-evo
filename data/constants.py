
GRID_WIDTH = 23
GRID_HEIGHT = 23
HEX_RADIUS = 30
HEX_DIAMETER = HEX_RADIUS * 2
FPS = 30
WIDTH = 2200
HEIGHT = 1100

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
GREEN = (0, 200, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0),
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
PINK = (255, 192, 203)
RED = (255, 0, 0)
CYAN = (0, 180, 200)
YELLOW = (255, 255, 0)
GOLD_DARK_GREEN = (34, 139, 34)
DARK_YELLOW = (204, 153, 0)

# Edge indices: clockwise from E = 0
DIRECTION_TO_EDGE = {
	"E": 0,
	"NE": 5,
	"NW": 4,
	"W": 3,
	"SW": 2,
	"SE": 1,
}

# Neighbor offsets for odd-r horizontal layout
EVEN_ROW_NEIGHBORS = {
	"E": (1, 0),
	"NE": (0, -1),
	"NW": (-1, -1),
	"W": (-1, 0),
	"SW": (-1, 1),
	"SE": (0, 1),
}

ODD_ROW_NEIGHBORS = {
	"E": (1, 0),
	"NE": (1, -1),
	"NW": (0, -1),
	"W": (-1, 0),
	"SW": (0, 1),
	"SE": (1, 1),
}

OPPOSITE_DIRECTION = {
	"E": "W",
	"NE": "SW",
	"NW": "SE",
	"W": "E",
	"SW": "NE",
	"SE": "NW",
}

#why differing brackets? { vs [
ERAS = [
    "Ancient",
    "Classical",
    "Medieval",
    "Renaissance",
    "Industrial",
    "Modern",
    "Atomic",
    "Information",
]

CITY_NAMES = [
	"Delhi",
	"Mumbai",
	"Vijayanagara",
	"Pataliputra",
	"Varanasi",
	"Agra",
	"Calcutta",
	"Lahore",
	"Bangalore",
	"Hyderabad",
	"Madurai",
	"Ahmedabad",
	"Kolhapur",
	"Prayaga",
	"Ayodhya",
	"Indraprastha",
	"Mathura",
	"Ujjain",
	"Gulbarga",
	"Jaunpur",
	"Rajagriha",
	"Sravasti",
	"Tiruchirapalli",
	"Thanjavur",
	"Bodhgaya",
	"Kushinagar",
	"Amaravati",
	"Gaur",
	"Gwalior",
	"Jaipur",
	"Karachi"
]
