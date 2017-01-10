from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from operator import itemgetter
import sys

if len(sys.argv) != 2:
    print "Usage: findtimewarpers.py height"
    exit(1)

# have a local running instance of zcashd
api = AuthServiceProxy("http://username:password@127.0.0.1:8232")

print "height,timestamp,miner,warplen,warpdelta"

maxheight = int(sys.argv[1])

warpcount = 0
impactedcount = 0
prevtimestamp = 0
t_list = []
miners = {}
maxwarplen = 0
maxwarpdelta = 0

# from block 0 to n (inclusive)
for h in xrange(0, maxheight+1):
    blockhash = api.getblockhash(h)
    block = api.getblock(blockhash)
    timestamp = block["time"]
    t_list.append(timestamp)

    if timestamp <= prevtimestamp:
        txid = block["tx"][0]
        tx = api.getrawtransaction(txid,1)
        vout = tx["vout"][0]
        miner = vout["scriptPubKey"]["addresses"][0]
        
        # how many previous blocks affected by this block?
        warplen = 0 
        for j in xrange(h-1, 0, -1):
            if timestamp <= t_list[j]:
                warplen = warplen + 1
            else:
                break
        
        impactedcount = impactedcount + warplen
        warpdelta = abs(timestamp - prevtimestamp)
        if warplen > maxwarplen:
            maxwarplen = warplen
        if warpdelta > maxwarpdelta:
            maxwarpdelta = warpdelta
        warpcount = warpcount + 1
        miners[miner] = miners.get(miner,0) + 1

        print "%d,%d,%s,%d,%d" % (h, timestamp, miner, warplen, warpdelta)

    prevtimestamp = timestamp

print "number of time warp blocks       = %d (%.2f%%)" % (warpcount, 100.0 * warpcount / maxheight)
print "number of affected blocks        = %d (%.2f%%)" % (impactedcount, 100.0 * impactedcount / maxheight)
print "longest chain of blocks warped   = %d" % maxwarplen
print "longest warp interval (secs)     = %d" % maxwarpdelta
print "miners and number of warp blocks = "
for k, v in sorted(miners.items(), key=itemgetter(1), reverse=True):
    print "%s,%d" % (k,v)

