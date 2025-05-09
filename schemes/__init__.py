from schemes.base import BaseScheme
from schemes.l2m import Least2Most
from schemes.sp import SuccessivePrompting
from schemes.sd import Selfdiscover

from schemes.cot import ChainofThought, ZeroCoT
from schemes.ps import PlanAndSolve
from schemes.cotsc import SelfconsistentCoT

from schemes.aot import AlgorithmofThought
from schemes.tot import TreeofThought
from schemes.top import TreeOfProblems
from schemes.got import GraphofThought

from schemes.knot import kNetworkofThought
from schemes.fiverknote import rkNetworkofThought


SCHEME_DICT = {
    'zero': ZeroFewShot,
    'few': ZeroFewShot,
    'l2m': Least2Most,
    'sp': SuccessivePrompting,
    'sd': Selfdiscover,
    'zerocot': ZeroCoT, #
    'ps': PlanAndSolve,
    'cot': ChainofThought, #
    'cotsc': SelfconsistentCoT, #
    'aot': AlgorithmofThought,
    'tot': TreeofThought, 
    'top': TreeOfProblems,
    'got': GraphofThought,
    'knot': kNetworkofThought, 
    'rknot': rkNetworkofThought,
}


def setup_scheme(args, task_loader):
    if args.scheme in SCHEME_DICT:
        return SCHEME_DICT[args.scheme](args, task_loader)
    else:
        raise NotImplementedError(f"prompt scheme {args.scheme} not implemented")