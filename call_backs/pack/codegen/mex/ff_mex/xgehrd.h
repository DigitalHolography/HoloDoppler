/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * xgehrd.h
 *
 * Code generation for function 'xgehrd'
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
void xgehrd(const emlrtStack *sp, emxArray_creal32_T *a, creal32_T tau_data[],
            int32_T *tau_size);

/* End of code generation (xgehrd.h) */
