/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * blockedSummation.h
 *
 * Code generation for function 'blockedSummation'
 *
 */

#pragma once

/* Include files */
#include "ff_mex_types.h"
#include "rtwtypes.h"
#include "emlrt.h"
#include "mex.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Function Declarations */
void colMajorFlatIter(const emlrtStack *sp, const emxArray_real32_T *x,
                      int32_T vlen, emxArray_real32_T *y);

/* End of code generation (blockedSummation.h) */
