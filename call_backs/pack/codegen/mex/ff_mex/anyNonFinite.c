/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * anyNonFinite.c
 *
 * Code generation for function 'anyNonFinite'
 *
 */

/* Include files */
#include "anyNonFinite.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include "mwmathutil.h"
#include <string.h>

/* Function Definitions */
boolean_T anyNonFinite(const emxArray_creal32_T *x)
{
  const creal32_T *x_data;
  int32_T k;
  int32_T nx;
  boolean_T p;
  x_data = x->data;
  nx = x->size[0] * x->size[1];
  p = true;
  for (k = 0; k < nx; k++) {
    if ((!p) || (muSingleScalarIsInf(x_data[k].re) ||
                 muSingleScalarIsInf(x_data[k].im) ||
                 (muSingleScalarIsNaN(x_data[k].re) ||
                  muSingleScalarIsNaN(x_data[k].im)))) {
      p = false;
    }
  }
  return !p;
}

/* End of code generation (anyNonFinite.c) */
