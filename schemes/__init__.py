# from schemes.base import BaseScheme
from schemes.cot import ChainofThought, ZeroCoT
# from schemes.tot import TreeofThought
# from schemes.got import GraphofThought
from schemes.knot import KnowledgeableNetworkofThought
from schemes.rknot import RKnowledgeableNetworkofThought
from schemes.fiverknote import FiveRKnowledgeableNetworkofThought



def setup_scheme(args, task_loader):
    if args.scheme == 'knot':
        return KnowledgeableNetworkofThought(args, task_loader)
    elif args.scheme == 'rknot':
        return RKnowledgeableNetworkofThought(args, task_loader)
    elif args.scheme == '5rknot':
        return FiveRKnowledgeableNetworkofThought(args, task_loader)
    elif args.scheme == 'cot':
        return ChainofThought(args, task_loader)
    elif args.scheme == 'zerocot':
        return ZeroCoT(args, task_loader)
    else:
        raise NotImplementedError(f"prompt scheme {args.scheme} not implemented")

    # if args.scheme == 'cot':
        # return ChainofThought(args)
    