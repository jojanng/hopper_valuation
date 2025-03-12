**TODO**

-**COMPLETED** prediction of single expected stock price (only for mu)
-**COMPLETED** intrinsic value calculator using DCF model (*revision might be needed*)
    analyzing price movements or earnings surprises using FFT will improve accuracy of intrinsic value model to detect longterm trend

-graphs: density x % and stock price prediction x pdf (full distribution)

-implement wider and more complex fft methods

-improve accuracy of valuation models (especially with higher fcf)

-write in documentation: differences between the both prediction algo
   carr madan fft uses fft to compute option and probabilities distributions and stock_price_algo predicts the stock price expected value at T

-**COMPLETED BUT NEEDS CONSTANT UPDATES** design website and functions (track options, predict stocks, easy technical analysis on stocks, etc)

-PROBLEMS:
    **FIXED BUT ACCURACY NOT 100%** check earning growth (negative weird example pltr is -29%) : negative earning growth leads to inaccurate data for intrinsic value

    