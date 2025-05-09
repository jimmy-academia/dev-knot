from schemes.base import BaseScheme
from schemes.cot import ChainofThought, ZeroCoT
# from schemes.tot import TreeofThought
# from schemes.got import GraphofThought
from schemes.knot import kNetworkofThought
from schemes.fiverknote import rkNetworkofThought


SCHEME_DICT = {
    'knot': kNetworkofThought, 
    'rknot': rkNetworkofThought,
    'zero': BaseScheme,
    'few': BaseScheme,
    'cot': ChainofThought,
}


def setup_scheme(args, task_loader):
    if args.scheme in SCHEME_DICT:
        return SCHEME_DICT[args.scheme](args, task_loader)
    else:
        raise NotImplementedError(f"prompt scheme {args.scheme} not implemented")