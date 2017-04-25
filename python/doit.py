import sys
import argparse
import re
import fnmatch
import sre_constants
from CLI import CLI


def _parseArgs(argv):
    parser = argparse.ArgumentParser(
        description="initialize port settings",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "command",
        help="doing commands"
    )
    parser.add_argument(
        "fq_ports",
        metavar="RBridgeID/0/PortNo",
        nargs="*",
        help='''VDX style port specification. You can spefy multiple ports.
ex: `10/0/1-3' or `10/0/1,2,3'

Also, you can multiple rbridge ID
ex: `10,20/0/3' or `10-12/0/3'
    `[12]0/0/3' or `1*/0/3' '''
    )
    parser.add_argument(
        "-r", "-b", "--rids",
        dest="rbridgeids",
        metavar="RBridgeID",
        action="append",
        help='''RBridgeID, You shuld use this option with `--port'.
This option is able to specify multiple RBridgeID.
ex: `-r 10'
    `-b 10,11,12'
    `--rids 10-12' '''
    )
    parser.add_argument(
        "--rids-pattern",
        dest="rids_pattern",
        metavar="RBridgeID_pattern",
        action="append",
        help='''RBridgeID pattern, You shuld use this option with `--port'.
This option is able to specify multiple RBridgeID by shell style pattern.
ex: `--rids-pattern 1[89]'
    `--rids-pattern *8' '''
    )
    parser.add_argument(
        "-p", "--port", "--ports",
        dest="ports",
        metavar="PortNo.",
        action="append",
        help='''Port No. You shuld use this option with `--rids' or `--rids-pattern'.
This option is able to specify multiple port No.
ex: `-p 1'
    `--port 1,2,3'
    `--ports 1-3' '''
    )

    args = parser.parse_args(argv)

    if not args.fq_ports and not args.ports and not args.rbridgeids:
        parser.error("Nothing argument was specified")

    if (not args.ports) != (not args.rbridgeids and not args.rids_pattern):
        if not args.rbridgeids and not args.rids_pattern:
            parser.error(
                "`--rids' or `--rids-pattern' option shuld be specified with `--ports' option")

        if not args.ports:
            parser.error(
                "`--ports' option shuld be specified with `--rids' and/or `--rids-pattern' option")

    if args.fq_ports:
        try:
            _checkFQPorts(args.fq_ports)
        except ValueError as err:
            parser.error("argument `{}' is invalid format".format(err))

    if args.rbridgeids:
        try:
            _checkNumbers(args.rbridgeids)
        except ValueError as err:
            parser.error("`--rids' option `{}' is invalid format".format(err))

    if args.rids_pattern:
        try:
            _checkRidsPattern(args.rids_pattern)
        except ValueError as err:
            parse.error("`--rids-pattern' option `{}' is invalid format".format(err))

    if args.ports:
        try:
            _checkNumbers(args.ports)
        except ValueError as err:
            parser.error("`--ports' option `{}' is invalid format".format(err))

    return args


def _checkFQPorts(fq_ports):
    for fq_port in fq_ports:
        e = fq_port.split("/")

        if len(e) != 3 or e[1] != "0":
            raise ValueError(fq_port)

        if '[' in e[0] or '?' in e[0] or '*' in e[0]:
            try:
                _checkRidsPattern([e[0]])
            except:
                raise ValueError(fq_port)
        else:
            try:
                _checkNumbers([e[0], e[2]])
            except:
                raise ValueError(fq_port)


def _checkNumbers(numbers):
    pattern1 = re.compile("^\d{1,3}(?:[-,]\d{1,3})*$", re.ASCII)
    for number in numbers:
        if not pattern1.match(number):
            raise ValueError(number)


def _checkRidsPattern(patterns):
    for pattern in patterns:
        try:
            fnmatch.fnmatch("", pattern)
        except sre_constants.error as e:
            raise ValueError(pattern)


def _breakupNumber(numbers):
    # from `1,3-5,9` breaks up to [1,3,4,5,9]
    if not numbers:
        return set()

    dest = set()
    for number in numbers:
        dest |= {int(x) for x in number.split(',') if '-' not in x}
        for r in re.findall("\d{1,3}-\d{1,3}", number, re.ASCII):
            (top, bottom) = r.split('-')
            top = int(top)
            bottom = int(bottom)
            if top > bottom:
                tmp = top
                top = bottom
                bottom = tmp
            dest |= set(range(top, bottom + 1))

    return dest


def _composeNumber(nums):
    prev = nums[0]
    dest = str(prev)
    cont = False
    tail = len(nums)
    for i in range(1, tail):
        num = nums[i]
        if 1 == num - prev:
            if 1 < tail - i:
                prev = num
                cont = True
                continue
            else:  # last loop
                dest += '-' + str(num)
                break

        if cont:
            dest += '-' + str(prev)

        dest += ',' + str(num)
        prev = num
        cont = False

    return dest


def _globRidsPattern(patterns):
    if not patterns:
        return set()

    vcs = CLI('show vcs', do_print=False)
    target = False
    rids = []
    for line in vcs.get_output():
        if not target:
            if re.match(r'-+$', line):
                target = True
            continue

        rids.append(line[0:line.find(' ')])

    return {int(x) for pattern in patterns for x in rids if fnmatch.fnmatch(x, pattern)}


def _genFqPorts(rbridgeids, ports):
    return {"%d/0/%s" % (r, p) for r in rbridgeids for p in ports}

if __name__ == '__main__':
    args = _parseArgs(sys.argv[1:])

    print(args)

    fqports = None

    if args.ports:
        rids = _breakupNumber(args.rbridgeids) | _globRidsPattern(args.rids_pattern)
        ports = _breakupNumber(args.ports)
        fqports = _genFqPorts(rids, ports)
    else:
        fqports = set()

    if args.fq_ports:
        for p in args.fq_ports:
            e = p.split("/")
            if '[' in e[0] or '?' in e[0] or '*' in e[0]:
                rids = _globRidsPattern([e[0]])
            else:
                rids = _breakupNumber([e[0]])

            ports = _breakupNumber([e[2]])

            fqports |= _genFqPorts(rids, ports)

    fqports = sorted(fqports)

    print(fqports)

    for fp in fqports:
        result = CLI(args.command % fp)

        for line in result.get_output():
            if re.search('syntax error', line, re.IGNORECASE):
                print("ERROR occured! Abort!!")
                sys.exit()
