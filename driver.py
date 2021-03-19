#!/usr/bin/env python3

import argparse




if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument(dest='argument1', help="This is the first argument")

	# Parse and print the results
	args = parser.parse_args()
	print(args.argument1)


