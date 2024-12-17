/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * linspace.c
 *
 * Code generation for function 'linspace'
 *
 */

/* Include files */
#include "linspace.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include "mwmathutil.h"
#include <string.h>

/* Variable Definitions */
static emlrtRTEInfo bb_emlrtRTEI = {
    33,         /* lineNo */
    37,         /* colNo */
    "linspace", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\linspace.m" /* pName
                                                                           */
};

static emlrtRTEInfo if_emlrtRTEI = {
    49,         /* lineNo */
    20,         /* colNo */
    "linspace", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\elmat\\linspace.m" /* pName
                                                                           */
};

/* Function Definitions */
void linspace(const emlrtStack *sp, real_T d2, real_T n, emxArray_real_T *y)
{
  real_T *y_data;
  int32_T k;
  if (!(n >= 0.0)) {
    if (muDoubleScalarIsNaN(n)) {
      emlrtErrorWithMessageIdR2018a(sp, &bb_emlrtRTEI,
                                    "Coder:toolbox:MustNotBeNaN",
                                    "Coder:toolbox:MustNotBeNaN", 3, 4, 1, "N");
    }
    y->size[0] = 1;
    y->size[1] = 0;
  } else {
    real_T delta1;
    int32_T i;
    delta1 = muDoubleScalarFloor(n);
    i = y->size[0] * y->size[1];
    y->size[0] = 1;
    y->size[1] = (int32_T)delta1;
    emxEnsureCapacity_real_T(sp, y, i, &if_emlrtRTEI);
    y_data = y->data;
    if ((int32_T)delta1 >= 1) {
      y_data[(int32_T)delta1 - 1] = d2;
      if (y->size[1] >= 2) {
        y_data[0] = 1.0;
        if (y->size[1] >= 3) {
          delta1 = (d2 - 1.0) / ((real_T)y->size[1] - 1.0);
          i = y->size[1];
          for (k = 0; k <= i - 3; k++) {
            y_data[k + 1] = ((real_T)k + 1.0) * delta1 + 1.0;
          }
        }
      }
    }
  }
}

/* End of code generation (linspace.c) */
