from milightsdriver.milight import Color, White

RED = Color(0, 100, 0)
GREEN = Color(85, 100, 0)
BLUE = Color(170, 100, 0)
CYAN = BLUE.mix(GREEN)
MAGENTA = BLUE.mix(RED)
YELLOW = RED.mix(GREEN)
ORANGE = RED.mix(YELLOW)

WHITE = White(50, 100)
WARM_WHITE = White(0, 100)
C_WARM_WHITE = Color(25, 100, 100)
COOL_WHITE = White(100, 100)
C_COOL_WHITE = Color(145, 100, 100)

