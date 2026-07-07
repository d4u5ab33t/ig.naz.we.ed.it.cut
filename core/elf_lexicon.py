from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# ELF-LEARNING LEXICON

GENRE_KW_SEED: Dict[str, List[str]] = {
    "electronic": ["techno","house","electro","synth","cyberpunk","drum","bass","dnb","edm",
                   "rave","club","bpm","beatdrop","laser","strobe","neon","robot","machine",
                   "kick","snare","sub","glitch","future","digital"],
    "hiphop":     ["hiphop","hip-hop","rap","trap","drill","underground","beat","flow",
                   "street","bavaria","munich","minga","corner","ganja","sesh","block",
                   "hood","grind","hustle","respekt","gang","crew","mic","freestyle",
                   "money","cash","kette","auto","bling","real","game","boss","szene"],
    "pop":        ["pop","chart","dance","synthpop","radio","hit","catchy","mainstream",
                    "party","tanzen","feiern","sommer","sonne"],
    "soul":       ["soul","rnb","blues","funk","jazz","groove","herz","seele","gefuehl",
                    "gefühl","zaertlich","zärtlich","sanft","warm"],
    "rock":       ["rock","metal","punk","guitar","grunge","indie","gitarre","riff",
                    "band","stage","buehne","bühne","distortion","wild","laut","rebell"],
}

MOOD_KW_SEED: Dict[str, List[str]] = {
    "happy":   ["happy","bright","vibrant","fun","summer","love","high","joy","smile",
                "sunshine","free","freedom","dance","celebrate","party","together",
                "gluecklich","glücklich","froh","freude","lachen","liebe","frei","freiheit",
                "sonne","sommer","tanzen","feiern","zusammen","hoffnung","hope","licht",
                "light","fly","flying","fliegen","leicht","schoen","schön","strahlen",
                "shine","gold","hell","farben","colors","juhu","yeah"],
    "intense": ["intense","dark","aggressive","hard","heavy","evil","gothic",
                "combat","battle","ruthless","insane","firewall","hass","hate","wut",
                "anger","kampf","fight","krieg","war","blut","blood","schmerz","pain",
                "angst","fear","dunkel","dark","schwarz","black","feuer","fire","brennen",
                "burn","zerbrochen","broken","allein","alone","einsam","lonely","schrei",
                "scream","wild","chaos","gefahr","danger","messer","gun","waffe",
                "toedlich","tödlich","rache","revenge","stolz","pride","macht","power",
                "hart","cold","kalt","eiskalt","brutal","laut","loud"],
    "calm":    ["calm","chill","atmospheric","slow","ambient","melancholic","peaceful","dreamy",
                "ruhig","stille","still","traurig","sad","tears","traenen","tränen","weinen",
                "cry","regen","rain","nacht","night","mond","moon","sterne","stars","himmel",
                "sky","meer","ocean","see","wolken","clouds","erinnerung","memory","vermissen",
                "miss","sehnsucht","longing","nostalgie","langsam","leise","quiet","frieden",
                "peace","atmen","breathe","warten","waiting","zeit","time","zuhause","home"],
}

LYRIC_STOPWORDS: set = {
    "der","die","das","den","dem","des","ein","eine","einen","einem","einer","eines",
    "und","oder","aber","doch","noch","auch","nur","schon","immer","nie","nicht","kein",
    "keine","ich","du","er","sie","es","wir","ihr","mich","dich","sich","uns","euch",
    "mein","meine","dein","deine","sein","seine","ihre","unser","euer","ist","war","sind",
    "war","waren","bin","bist","hat","hab","habe","haben","hatte","werde","wirst","wird",
    "werden","kann","kannst","koennen","können","muss","musst","muessen","müssen","soll",
    "sollst","sollen","will","willst","wollen","mag","moechte","möchte","auf","in","an",
    "am","im","zu","zur","zum","von","vom","mit","bei","nach","aus","fuer","für","um",
    "durch","gegen","ohne","ueber","über","unter","vor","hinter","neben","zwischen","so",
    "wie","was","wer","wo","wann","warum","weil","dass","damit","als","wenn","dann","hier",
    "da","dort","jetzt","heute","this","that","these","those","the","a","an","and","or",
    "but","not","no","yes","i","you","he","she","it","we","they","me","him","her","us",
    "them","my","your","his","its","our","their","is","was","were","am","are","be","been",
    "being","have","has","had","will","would","can","could","should","shall","may","might",
    "must","do","does","did","to","of","in","on","at","by","for","with","about","against",
    "between","into","through","during","before","after","above","below","from","up","down",
    "so","than","too","very","just","now","here","there","when","where","why","how","all",
    "each","few","more","most","other","some","such","only","own","same","oh","yeah","uh",
    "na","hey","ah","la","yo",
}


@dataclass
class DirectorStyle:
    name: str
    description: str
    transient_sensitivity: float = 1.0
    stutter_frac: float = 0.22
    stutter_reps: int = 2
    stutter_every: int = 4
    preferred_effects: List[str] = field(default_factory=list)
    effect_intensity: float = 1.0
    motion_sync_strength: float = 0.45
    motion_speed_range: Tuple[float, float] = (0.72, 1.45)
    zoom_sensitivity: float = 0.25
    hold_beats: Tuple[int, int] = (6, 12)
    chroma_preference: float = 0.0

    def to_config_overrides(self) -> dict:
        return {
            "stutter_frac": self.stutter_frac,
            "stutter_reps": self.stutter_reps,
            "stutter_every": self.stutter_every,
            "motion_sync_strength": self.motion_sync_strength,
            "motion_sync_min_speed": self.motion_speed_range[0],
            "motion_sync_max_speed": self.motion_speed_range[1],
            "audio_scale_strength": self.zoom_sensitivity,
            "min_hold_beats": self.hold_beats[0],
            "max_hold_beats": self.hold_beats[1],
        }


DIRECTOR_STYLES = {
    "cunningham": DirectorStyle(
        name="cunningham",
        description="Chris Cunningham – Präziser Audio-Sync, mechanische Zuckungen, düstere Ästhetik",
        transient_sensitivity=0.8,
        stutter_frac=0.10,
        stutter_reps=2,
        stutter_every=6,
        preferred_effects=["glitch_rgb", "stutter_strong", "flash_white", "vinyl_scratch", "glitch_strong"],
        effect_intensity=0.3,
        motion_sync_strength=0.5,
        motion_speed_range=(0.8, 1.3),
        zoom_sensitivity=0.2,
        hold_beats=(8, 16),
        chroma_preference=0.3,
    ),
    "gondry": DirectorStyle(
        name="gondry",
        description="Michel Gondry – Handgemachte Illusionen, strukturelle Pattern, analoge Ästhetik",
        transient_sensitivity=0.6,
        stutter_frac=0.06,
        stutter_reps=2,
        stutter_every=8,
        preferred_effects=["pixelate", "stop_motion", "fisheye", "vignette", "slowmo"],
        effect_intensity=0.2,
        motion_sync_strength=0.3,
        motion_speed_range=(0.85, 1.15),
        zoom_sensitivity=0.15,
        hold_beats=(12, 20),
        chroma_preference=0.1,
    ),
    "jonze": DirectorStyle(
        name="jonze",
        description="Spike Jonze – Physisches Pacing, One-Shot-Choreographie, organische Bewegung",
        transient_sensitivity=0.7,
        stutter_frac=0.05,
        stutter_reps=2,
        stutter_every=7,
        preferred_effects=["whip_pan", "flash_cut", "speed_ramp", "hq_sharp", "cinema_grade"],
        effect_intensity=0.3,
        motion_sync_strength=0.6,
        motion_speed_range=(0.75, 1.4),
        zoom_sensitivity=0.25,
        hold_beats=(8, 14),
        chroma_preference=0.2,
    ),
    "hype_williams": DirectorStyle(
        name="hype_williams",
        description="Hype Williams – Fisheye, Neon-Farben, hochgesättigte Hip-Hop-Ästhetik der 90er",
        transient_sensitivity=0.7,
        stutter_frac=0.08,
        stutter_reps=2,
        stutter_every=6,
        preferred_effects=["neon_flash", "colorshift", "fisheye", "overexpose", "mirror_hue", "pulse_glow"],
        effect_intensity=0.3,
        motion_sync_strength=0.4,
        motion_speed_range=(0.8, 1.3),
        zoom_sensitivity=0.3,
        hold_beats=(8, 14),
        chroma_preference=0.4,
    ),
    "rl_director": DirectorStyle(
        name="rl_director",
        description="RL-Bandit AI Director – Lernt selbstständig den besten Stil für jedes Genre",
        transient_sensitivity=0.7,
        stutter_frac=0.10,
        stutter_reps=2,
        stutter_every=6,
        preferred_effects=[],
        effect_intensity=0.3,
        motion_sync_strength=0.4,
        motion_speed_range=(0.8, 1.3),
        zoom_sensitivity=0.2,
        hold_beats=(8, 14),
        chroma_preference=0.2,
    ),
}

GENRE_DIRECTOR_PRIORITIES = {
    "electronic": ["cunningham", "jonze", "hype_williams", "gondry", "rl_director"],
    "hiphop": ["hype_williams", "jonze", "cunningham", "rl_director", "gondry"],
    "pop": ["gondry", "hype_williams", "jonze", "cunningham", "rl_director"],
    "soul": ["gondry", "jonze", "cunningham", "hype_williams", "rl_director"],
    "rock": ["jonze", "cunningham", "gondry", "hype_williams", "rl_director"],
    "other": ["rl_director", "jonze", "cunningham", "gondry", "hype_williams"],
}

DIRECTOR_EFFECT_WEIGHTS = {
    "cunningham": {
        "glitch_rgb": 1.5, "stutter_strong": 1.5, "flash_white": 1.3,
        "vinyl_scratch": 1.4, "glitch_strong": 1.6, "datamosh": 1.2,
    },
    "gondry": {
        "pixelate": 1.5, "stop_motion": 1.6, "fisheye": 1.3,
        "vignette": 1.4, "slowmo": 1.5, "crossfade": 1.2,
    },
    "jonze": {
        "whip_pan": 1.5, "flash_cut": 1.4, "speed_ramp": 1.5,
        "hq_sharp": 1.3, "cinema_grade": 1.4, "pulse_glow": 1.2,
    },
    "hype_williams": {
        "neon_flash": 1.6, "colorshift": 1.5, "fisheye": 1.5,
        "overexpose": 1.4, "mirror_hue": 1.4, "pulse_glow": 1.3,
    },
}

# Banner placeholders (fill with actual banner strings elsewhere if needed)
BANNER_WE_ED = "WE.ED.IT"
BANNER_BEAT_SYNC = "BeatSync"
BANNER_OIDASHEIM = "Oidasheim"
BANNER_IGNAZ = "Ignaz"
BANNER_CUT_IT = "CutIt"
BANNER_CLAW = "Claw"
BANNER_DIREKTOR = "Direktor"
BANNER_RENDER = "Render"
BANNER_TRAP = "Trap"
BANNER_DRILL = "Drill"
BANNER_UNDERGROUND = "Underground"
BANNER_NFO = "NFO"
BANNER_MINGA = "Minga"
BANNER_RAW = "RawVids"
BANNER_EYECANDY = "EyeCandy"
BANNER_9D = "9D"
BANNER_DONE = "Done"
BANNER_ERROR = "Error"
BANNER_OK = "OK"
BANNER_BOOT = "Boot"

ALL_BANNERS = {
    "we_ed":       BANNER_WE_ED,
    "beat_sync":   BANNER_BEAT_SYNC,
    "oidasheim":   BANNER_OIDASHEIM,
    "ignaz":       BANNER_IGNAZ,
    "cut_it":      BANNER_CUT_IT,
    "claw":        BANNER_CLAW,
    "direktor":    BANNER_DIREKTOR,
    "render":      BANNER_RENDER,
    "trap":        BANNER_TRAP,
    "drill":       BANNER_DRILL,
    "underground": BANNER_UNDERGROUND,
    "nfo":         BANNER_NFO,
    "minga":       BANNER_MINGA,
    "raw_vidz":    BANNER_RAW,
    "eyecandy":    BANNER_EYECANDY,
    "9d_semantic": BANNER_9D,
    "done":        BANNER_DONE,
    "error":       BANNER_ERROR,
    "ok":          BANNER_OK,
    "boot":        BANNER_BOOT,
}


# VIRTUAL CAMERA (16 Moves)
CAMERA_MOVES = {
    "dolly_in": {"zoom_start":1.0,"zoom_end":1.25,"x_start":0.5,"y_start":0.5,"suitable":["verse","chorus","intro"],"energy_min":0.3,"energy_max":0.9},
    "dolly_out": {"zoom_start":1.25,"zoom_end":1.0,"x_start":0.5,"y_start":0.5,"suitable":["verse","outro","bridge"],"energy_min":0.2,"energy_max":0.8},
    "dolly_zoom": {"zoom_start":1.0,"zoom_end":1.4,"scale_start":1.0,"scale_end":0.85,"suitable":["chorus","bridge"],"energy_min":0.7,"energy_max":1.0},
    "crane_up": {"zoom_start":1.2,"zoom_end":1.0,"x_start":0.5,"y_start":0.7,"x_end":0.5,"y_end":0.3,"suitable":["chorus","outro"],"energy_min":0.5,"energy_max":1.0},
    "crane_down": {"zoom_start":1.0,"zoom_end":1.2,"x_start":0.5,"y_start":0.3,"x_end":0.5,"y_end":0.7,"suitable":["intro","verse"],"energy_min":0.2,"energy_max":0.7},
    "orbital_left": {"zoom_start":1.15,"zoom_end":1.15,"x_start":0.6,"y_start":0.5,"x_end":0.4,"y_end":0.5,"orbit":True,"suitable":["chorus","verse"],"energy_min":0.4,"energy_max":0.9},
    "orbital_right": {"zoom_start":1.15,"zoom_end":1.15,"x_start":0.4,"y_start":0.5,"x_end":0.6,"y_end":0.5,"orbit":True,"suitable":["chorus","verse"],"energy_min":0.4,"energy_max":0.9},
    "whip_pan_left": {"zoom_start":1.0,"zoom_end":1.0,"x_start":0.8,"y_start":0.5,"x_end":0.2,"y_end":0.5,"blur":8,"speed":3.0,"suitable":["chorus","bridge"],"energy_min":0.6,"energy_max":1.0},
    "whip_pan_right": {"zoom_start":1.0,"zoom_end":1.0,"x_start":0.2,"y_start":0.5,"x_end":0.8,"y_end":0.5,"blur":8,"speed":3.0,"suitable":["chorus","bridge"],"energy_min":0.6,"energy_max":1.0},
    "dutch_angle": {"rotation":8,"suitable":["bridge","chorus"],"energy_min":0.5,"energy_max":1.0},
    "rack_focus_near": {"blur_start":3.0,"blur_end":0.0,"suitable":["verse","bridge"],"energy_min":0.2,"energy_max":0.7},
    "rack_focus_far": {"blur_start":0.0,"blur_end":3.0,"suitable":["verse","bridge"],"energy_min":0.2,"energy_max":0.7},
    "tilt_shift": {"strength":0.6,"suitable":["intro","outro"],"energy_min":0.1,"energy_max":0.5},
    "perspective_tilt": {"warp_strength":0.15,"suitable":["chorus","bridge"],"energy_min":0.5,"energy_max":0.9},
    "parallax_3d": {"zoom_start":1.1,"zoom_end":1.15,"warp_strength":0.1,"suitable":["verse","chorus"],"energy_min":0.3,"energy_max":0.8},
    "hero_static": {"zoom_start":1.05,"zoom_end":1.06,"x_start":0.5,"y_start":0.5,"suitable":["intro","outro","bridge"],"energy_min":0.1,"energy_max":0.6}
}
