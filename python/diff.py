import sys
import argparse
import difflib
import re
from CLI import CLI


####################################################
## work arround `autojunk' behavior
####################################################
def new__init__(self, isjunk=None, a='', b='', autojunk=False):
    self.isjunk = isjunk
    self.a = self.b = None
    self.autojunk = autojunk
    self.set_seqs(a, b)
difflib.SequenceMatcher.__init__ = new__init__
####################################################


def _parseArgs(argv):
    parser = argparse.ArgumentParser(
        description="diff two file or command's result",
    )
    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "-u",
        dest="style",
        action="store_const",
        const="u",
        default="u",
        help="unified diff style, default"
    )
    group.add_argument(
        "-c",
        dest="style",
        action="store_const",
        const="c",
        help="context diff style"
    )
    group.add_argument(
        "-n",
        dest="style",
        action="store_const",
        const="n",
        help="differ diff style"
    )
    parser.add_argument(
        "-l",
        dest="line",
        metavar="N",
        action="store",
        type=int,
        default=3,
        help="number of result lines. default value is 3. It can use with `-u' or `-c' option."
    )

    parser.add_argument(
        "left",
        help='''
diff left source. When it starts with "f:", rest part treat as file name and read lines form it.
Otherwise, it treat as VDX CLI command, and use outputs of the command as diff source.
If you want to quote it, use "(double quote)'''
    )

    parser.add_argument(
        "right",
        help="diff right source. You specify file or command like `left'"
    )

    return parser.parse_args(argv)

if __name__ == '__main__':
    args = _parseArgs(sys.argv[1:])

    if args.left[:2] == 'f:':
        f = open(args.left[2:])
        left = [l.rstrip("\r\n") for l in f]
        f.close()
    else:
        left = CLI(args.left, do_print=False).output.splitlines()
        for line in left:
            if re.search('syntax error', line):
                print("ERROR occured in left command! Abort!!")
                print(args.left)
                for l in left:
                    print(l)
                sys.exit()

    if args.right[:2] == 'f:':
        f = open(args.right[2:])
        right = [l.rstrip("\r\n") for l in f]
        f.close()
    else:
        right = CLI(args.right, do_print=False).output.splitlines()
        for line in right:
            if re.search('syntax error', line):
                print("ERROR occured in right command! Abort!!")
                print(args.right)
                for l in right:
                    print(l)
                sys.exit()

    if args.style == "u":
        diff = difflib.unified_diff(left, right, fromfile=args.left, tofile=args.right, n=args.line)
    elif args.style == "c":
        diff = difflib.context_diff(left, right, fromfile=args.left, tofile=args.right, n=args.line)
    elif args.style == "n":
        diff = difflib.ndiff(left, right)

    for line in diff:
        print(line)
