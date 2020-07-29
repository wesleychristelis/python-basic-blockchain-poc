from functools import reduce 

def sum_reducer(amounts):
    return reduce(lambda tx_sum, tx_amt : tx_sum + sum(tx_amt) if(len(tx_amt) > 0) else tx_sum + 0, amounts, 0)
