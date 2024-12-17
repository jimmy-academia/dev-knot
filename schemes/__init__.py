# from schemes.base import BaseScheme
# from schemes.cot import ChainofThought
# from schemes.tot import TreeofThought
# from schemes.got import GraphofThought
from schemes.knot import KnowledgeableNetworkofThought


def setup_scheme(args, task_loader):
    if args.scheme == 'knot':
        return KnowledgeableNetworkofThought(args, task_loader)
    else:
        raise NotImplementedError(f"prompt scheme {args.scheme} not implemented")

    # if args.scheme == 'cot':
        # return ChainofThought(args)
    