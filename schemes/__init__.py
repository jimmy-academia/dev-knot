from schemes.base import ZeroFewShot
from schemes.l2m import Least2Most
from schemes.sp import SuccessivePrompting
from schemes.sd import Selfdiscover

from schemes.ps import PlanAndSolve
from schemes.cot import ChainofThought, ZeroCoT, SelfConsistentCoT

from schemes.aot import AlgorithmofThought
# from schemes.tot import TreeofThought
from schemes.top import TreeOfProblems
from schemes.got import GraphofThought

from schemes.knot import kNetworkofThought
from schemes.rknot import rkNetworkofThought


SCHEME_DICT = {
    'zero': ZeroFewShot,
    'few': ZeroFewShot,
    'l2m': Least2Most,
    'sp': SuccessivePrompting,
    'sd': Selfdiscover,
    'zerocot': ZeroCoT,
    'ps': PlanAndSolve,
    'cot': ChainofThought, 
    'cotsc': SelfConsistentCoT,
    'aot': AlgorithmofThought,
    # 'tot': TreeofThought, 
    'top': TreeOfProblems,
    'got': GraphofThought, ## run in Graph-of-thought for yelp
    'knot': kNetworkofThought, 
    'rknot': rkNetworkofThought,
}


def setup_scheme(args, task_loader):
    if args.scheme in SCHEME_DICT:
        return SCHEME_DICT[args.scheme](args, task_loader)
    else:
        raise NotImplementedError(f"prompt scheme {args.scheme} not implemented")