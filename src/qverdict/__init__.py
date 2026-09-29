"""QVerdict: sound, anytime-valid, three-valued test oracles for quantum programs."""
from .circuits import Circuit, gate
from .pauli import Pauli, StabilizerGroup, stabilizer_generators
from .simulator import NoiseModel, IDEAL, density_matrix, statevector
from .plans import make_target, cover_plan, z_plan, exact_case
from .oracles import ORACLES, OracleConfig, run_oracle, PASS, FAIL, INC

__version__ = "1.0.0"
