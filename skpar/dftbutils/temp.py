"""Temporary hack to see how tasks can make use of refdata"""

def temptask(implargs, database, *args, **kwargs):
    """just another task with a trivial signature"""
    refdata = implargs['refdata']
