"""Trivial user module."""

def userfunc(say='Hi'):
    """Test func with one parameter."""
    return 'SKPAR says {}'.format(say)

TASKDICT = {'greet': userfunc}
