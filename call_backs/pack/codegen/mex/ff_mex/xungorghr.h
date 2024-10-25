/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * xungorghr.h
 *
 * Code generation for function 'xungorghr'
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
void xungorghr(const emlrtStack *sp, int32_T n, int32_T ihi,
               emxArray_creal32_T *A, int32_T lda, const creal32_T tau_data[]);

/* End of code generation (xungorghr.h) */
