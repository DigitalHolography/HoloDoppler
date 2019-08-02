#include "mex.h"

#include <stddef.h>
#include <stdint.h>

void mexFunction(int nlhs, mxArray *plhs[], int nrhs,
                 const mxArray *prhs[])
{
    if (nrhs != 2)
    {
        mexErrMsgIdAndTxt("MyToolbox:lib:nrhs", "Two inputs required");
    }

    if (nlhs != 0)
    {
        mexErrMsgIdAndTxt("MyToolbox:lib:nlhs", "No output");
    }

    mxUint8 *in = mxGetUint8s(prhs[0]);
    mxSingle *out = mxGetSingles(prhs[1]);
    mwSize in_len = mxGetNumberOfElements(prhs[0]);
    mwSize out_len = mxGetNumberOfElements(prhs[1]);

    // if (in_len / 5 != out_len)
    // {
    //     mexErrMsgIdAndTxt("MyToolbox:lib:prhs", "input and output have different sizes");
    // }

    if (in_len % 3 != 0)
    {
        mexErrMsgIdAndTxt("MyToolbox:lib:prhs", "input must containt a multiple of 3 bytes");
    }

    uint16_t b0 = 0;
    uint16_t b1 = 0;
    uint16_t b2 = 0;

    uint16_t u1 = 0;
    uint16_t u2 = 0;

    for (size_t i = 0; i < in_len / 3; ++i)
    {
        b0 = in[3 * i];
        b1 = in[3 * i + 1];
        b2 = in[3 * i + 2];

        u1 = (b0 << 4) + (b1 >> 4);
        u2 = ((b1 & 0b00001111) >> 4) + (b2 << 4);

        out[2 * i] = u1;
        out[2 * i + 1] = u2;
    }
}