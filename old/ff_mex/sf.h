/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * sf.h
 *
 * Code generation for function 'sf'
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
void b_sf(const emlrtStack *sp, emxArray_creal32_T *H, real_T threshold);

void sf(const emlrtStack *sp, emxArray_creal32_T *H, real_T threshold);

/* End of code generation (sf.h) */
