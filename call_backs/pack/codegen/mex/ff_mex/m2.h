/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * m2.h
 *
 * Code generation for function 'm2'
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
void m2(const emlrtStack *sp, emxArray_real32_T *SH, real_T f1, real_T f2,
        real_T fs, real_T batch_size, real_T gw, emxArray_real32_T *M2);

/* End of code generation (m2.h) */
