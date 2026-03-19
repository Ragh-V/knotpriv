This file addresses the process for getting the necessary HFK data for 16-crossing knots. Most notably, the precise n-values are not precomputed; instead, we obtain bounds on these values.

"HFK-m.sage"
This script uses SnapPy to calculate the knot Floer homology of each knot in the numDTList. It then uses the epsilon and tau values to calculate the m-values, and it saves the m-values to a file called 'mList.txt'. For later use, it also saves a list of ranks of HFK, named 'HFKrankList.txt'. (For good measure, it also saves the epsilon and tau values to lists called 'epsilonList.txt' and 'tauList.txt'.)

"HFK-nBounds.sage"
This script uses the m-value and rank of HFK to bound the n-value of each knot from below. It outputs 'nBoundList.txt'.
