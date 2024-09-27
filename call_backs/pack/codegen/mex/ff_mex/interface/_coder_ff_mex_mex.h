/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * _coder_ff_mex_mex.h
 *
 * Code generation for function '_coder_ff_mex_mex'
 *
 */

#pragma once

/* Include files */
#include "rtwtypes.h"
#include "emlrt.h"
#include "mex.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Function Declarations */
void ff_mexFunction(int32_T nlhs, mxArray *plhs[1], int32_T nrhs,
                    const mxArray *prhs[2]);

void m0_mexFunction(int32_T nlhs, mxArray *plhs[1], int32_T nrhs,
                    const mxArray *prhs[6]);

void m1_mexFunction(int32_T nlhs, mxArray *plhs[1], int32_T nrhs,
                    const mxArray *prhs[6]);

void m2_mexFunction(int32_T nlhs, mxArray *plhs[1], int32_T nrhs,
                    const mxArray *prhs[6]);

MEXFUNCTION_LINKAGE void mexFunction(int32_T nlhs, mxArray *plhs[],
                                     int32_T nrhs, const mxArray *prhs[]);

emlrtCTX mexFunctionCreateRootTLS(void);

void ri_mexFunction(int32_T nlhs, mxArray *plhs[1], int32_T nrhs,
                    const mxArray *prhs[8]);

void sf_mexFunction(int32_T nlhs, mxArray *plhs[1], int32_T nrhs,
                    const mxArray *prhs[2]);

void sfx_mexFunction(int32_T nlhs, mxArray *plhs[1], int32_T nrhs,
                     const mxArray *prhs[3]);

/* End of code generation (_coder_ff_mex_mex.h) */
