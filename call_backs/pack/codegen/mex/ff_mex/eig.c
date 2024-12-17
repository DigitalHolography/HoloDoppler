/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * eig.c
 *
 * Code generation for function 'eig'
 *
 */

/* Include files */
#include "eig.h"
#include "anyNonFinite.h"
#include "ff_mex_emxutil.h"
#include "ff_mex_types.h"
#include "rt_nonfinite.h"
#include "schur.h"
#include "warning.h"
#include "xgeev.h"
#include <string.h>

/* Variable Definitions */
static emlrtRSInfo eh_emlrtRSI = {
    93,    /* lineNo */
    "eig", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\eig.m" /* pathName
                                                                       */
};

static emlrtRSInfo fh_emlrtRSI = {
    102,   /* lineNo */
    "eig", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\eig.m" /* pathName
                                                                       */
};

static emlrtRSInfo gh_emlrtRSI = {
    137,   /* lineNo */
    "eig", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\eig.m" /* pathName
                                                                       */
};

static emlrtRSInfo hh_emlrtRSI = {
    145,   /* lineNo */
    "eig", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\eig.m" /* pathName
                                                                       */
};

static emlrtRSInfo ih_emlrtRSI = {
    153,   /* lineNo */
    "eig", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\eig.m" /* pathName
                                                                       */
};

static emlrtRSInfo jh_emlrtRSI = {
    32,                     /* lineNo */
    "eigHermitianStandard", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\private\\eigHerm"
    "itianStandard.m" /* pathName */
};

static emlrtRSInfo kh_emlrtRSI = {
    33,                     /* lineNo */
    "eigHermitianStandard", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\private\\eigHerm"
    "itianStandard.m" /* pathName */
};

static emlrtRSInfo ci_emlrtRSI = {
    20,                         /* lineNo */
    "eigSkewHermitianStandard", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\private\\eigSkew"
    "HermitianStandard.m" /* pathName */
};

static emlrtRSInfo di_emlrtRSI = {
    29,                                /* lineNo */
    "eigComplexSkewHermitianStandard", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\private\\eigComp"
    "lexSkewHermitianStandard.m" /* pathName */
};

static emlrtRSInfo hi_emlrtRSI = {
    59,            /* lineNo */
    "eigStandard", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\private\\eigStan"
    "dard.m" /* pathName */
};

static emlrtRSInfo ii_emlrtRSI = {
    33,            /* lineNo */
    "eigStandard", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\private\\eigStan"
    "dard.m" /* pathName */
};

static emlrtRSInfo ji_emlrtRSI = {
    31,            /* lineNo */
    "eigStandard", /* fcnName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\private\\eigStan"
    "dard.m" /* pathName */
};

static emlrtRTEInfo y_emlrtRTEI = {
    62,    /* lineNo */
    27,    /* colNo */
    "eig", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\eig.m" /* pName
                                                                       */
};

static emlrtRTEInfo ve_emlrtRTEI = {
    68,    /* lineNo */
    24,    /* colNo */
    "eig", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\eig.m" /* pName
                                                                       */
};

static emlrtRTEInfo we_emlrtRTEI = {
    72,    /* lineNo */
    28,    /* colNo */
    "eig", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\eig.m" /* pName
                                                                       */
};

static emlrtRTEInfo xe_emlrtRTEI = {
    97,    /* lineNo */
    9,     /* colNo */
    "eig", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\eig.m" /* pName
                                                                       */
};

static emlrtRTEInfo ye_emlrtRTEI = {
    101,   /* lineNo */
    13,    /* colNo */
    "eig", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\eig.m" /* pName
                                                                       */
};

static emlrtRTEInfo af_emlrtRTEI =
    {
        76,                  /* lineNo */
        13,                  /* colNo */
        "eml_mtimes_helper", /* fName */
        "C:\\Program "
        "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\ops\\eml_mtimes_"
        "helper.m" /* pName */
};

static emlrtRTEInfo bf_emlrtRTEI = {
    32,            /* lineNo */
    13,            /* colNo */
    "eigStandard", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022b\\toolbox\\eml\\lib\\matlab\\matfun\\private\\eigStan"
    "dard.m" /* pName */
};

/* Function Definitions */
void eig(const emlrtStack *sp, const emxArray_creal32_T *A,
         emxArray_creal32_T *V, emxArray_creal32_T *D)
{
  emlrtStack b_st;
  emlrtStack c_st;
  emlrtStack st;
  emxArray_creal32_T *r;
  creal32_T dt_data[2048];
  const creal32_T *A_data;
  creal32_T *D_data;
  int32_T b_i;
  int32_T i;
  int32_T j;
  int32_T n;
  st.prev = sp;
  st.tls = sp->tls;
  b_st.prev = &st;
  b_st.tls = st.tls;
  c_st.prev = &b_st;
  c_st.tls = b_st.tls;
  A_data = A->data;
  emlrtHeapReferenceStackEnterFcnR2012b((emlrtConstCTX)sp);
  n = A->size[0];
  if (A->size[0] != A->size[1]) {
    emlrtErrorWithMessageIdR2018a(sp, &y_emlrtRTEI,
                                  "MATLAB:eig:inputMustBeSquareStandard",
                                  "MATLAB:eig:inputMustBeSquareStandard", 0);
  }
  i = V->size[0] * V->size[1];
  V->size[0] = A->size[0];
  V->size[1] = A->size[0];
  emxEnsureCapacity_creal32_T(sp, V, i, &ve_emlrtRTEI);
  i = D->size[0] * D->size[1];
  D->size[0] = A->size[0];
  D->size[1] = A->size[0];
  emxEnsureCapacity_creal32_T(sp, D, i, &we_emlrtRTEI);
  if ((A->size[0] != 0) && (A->size[1] != 0)) {
    st.site = &eh_emlrtRSI;
    if (anyNonFinite(A)) {
      i = V->size[0] * V->size[1];
      V->size[0] = A->size[0];
      V->size[1] = A->size[0];
      emxEnsureCapacity_creal32_T(sp, V, i, &xe_emlrtRTEI);
      D_data = V->data;
      j = A->size[0] * A->size[0];
      for (i = 0; i < j; i++) {
        D_data[i].re = rtNaNF;
        D_data[i].im = 0.0F;
      }
      i = D->size[0] * D->size[1];
      D->size[0] = A->size[0];
      D->size[1] = A->size[0];
      emxEnsureCapacity_creal32_T(sp, D, i, &ye_emlrtRTEI);
      D_data = D->data;
      j = A->size[0] * A->size[0];
      for (i = 0; i < j; i++) {
        D_data[i].re = 0.0F;
        D_data[i].im = 0.0F;
      }
      st.site = &fh_emlrtRSI;
      for (j = 0; j < n; j++) {
        D_data[j + D->size[0] * j].re = rtNaNF;
        D_data[j + D->size[0] * j].im = 0.0F;
      }
    } else {
      int32_T exitg1;
      boolean_T exitg2;
      boolean_T p;
      p = (A->size[0] == A->size[1]);
      if (p) {
        j = 0;
        exitg2 = false;
        while ((!exitg2) && (j <= A->size[1] - 1)) {
          b_i = 0;
          do {
            exitg1 = 0;
            if (b_i <= j) {
              if ((!(A_data[b_i + A->size[0] * j].re ==
                     A_data[j + A->size[0] * b_i].re)) ||
                  (!(A_data[b_i + A->size[0] * j].im ==
                     -A_data[j + A->size[0] * b_i].im))) {
                p = false;
                exitg1 = 1;
              } else {
                b_i++;
              }
            } else {
              j++;
              exitg1 = 2;
            }
          } while (exitg1 == 0);
          if (exitg1 == 1) {
            exitg2 = true;
          }
        }
      }
      if (p) {
        st.site = &gh_emlrtRSI;
        b_st.site = &jh_emlrtRSI;
        schur(&b_st, A, V, D);
        D_data = D->data;
        b_st.site = &kh_emlrtRSI;
        n = D->size[0];
        D_data[0].im = 0.0F;
        for (j = 2; j <= n; j++) {
          D_data[(j + D->size[0] * (j - 1)) - 1].im = 0.0F;
          D_data[(j + D->size[0] * (j - 2)) - 1].re = 0.0F;
          D_data[(j + D->size[0] * (j - 2)) - 1].im = 0.0F;
          for (b_i = 0; b_i <= j - 2; b_i++) {
            D_data[b_i + D->size[0] * (j - 1)].re = 0.0F;
            D_data[b_i + D->size[0] * (j - 1)].im = 0.0F;
          }
        }
      } else {
        p = (A->size[0] == A->size[1]);
        if (p) {
          j = 0;
          exitg2 = false;
          while ((!exitg2) && (j <= A->size[1] - 1)) {
            b_i = 0;
            do {
              exitg1 = 0;
              if (b_i <= j) {
                if ((!(A_data[b_i + A->size[0] * j].re ==
                       -A_data[j + A->size[0] * b_i].re)) ||
                    (!(A_data[b_i + A->size[0] * j].im ==
                       A_data[j + A->size[0] * b_i].im))) {
                  p = false;
                  exitg1 = 1;
                } else {
                  b_i++;
                }
              } else {
                j++;
                exitg1 = 2;
              }
            } while (exitg1 == 0);
            if (exitg1 == 1) {
              exitg2 = true;
            }
          }
        }
        if (p) {
          real32_T f;
          st.site = &hh_emlrtRSI;
          b_st.site = &ci_emlrtRSI;
          emxInit_creal32_T(&b_st, &r, 2, &af_emlrtRTEI);
          i = r->size[0] * r->size[1];
          r->size[0] = A->size[0];
          r->size[1] = A->size[1];
          emxEnsureCapacity_creal32_T(&b_st, r, i, &af_emlrtRTEI);
          D_data = r->data;
          j = A->size[0] * A->size[1];
          for (i = 0; i < j; i++) {
            D_data[i].re = 0.0F * A_data[i].re - A_data[i].im;
            D_data[i].im = 0.0F * A_data[i].im + A_data[i].re;
          }
          c_st.site = &di_emlrtRSI;
          schur(&c_st, r, V, D);
          D_data = D->data;
          emxFree_creal32_T(&b_st, &r);
          n = D->size[0];
          f = D_data[0].re;
          D_data[0].re = 0.0F;
          D_data[0].im = -f;
          for (j = 2; j <= n; j++) {
            f = D_data[(j + D->size[0] * (j - 1)) - 1].re;
            D_data[(j + D->size[0] * (j - 1)) - 1].re = 0.0F;
            D_data[(j + D->size[0] * (j - 1)) - 1].im = -f;
            for (b_i = 0; b_i <= j - 2; b_i++) {
              D_data[b_i + D->size[0] * (j - 1)].re = 0.0F;
              D_data[b_i + D->size[0] * (j - 1)].im = 0.0F;
            }
          }
        } else {
          st.site = &ih_emlrtRSI;
          n = A->size[0];
          b_st.site = &ji_emlrtRSI;
          xgeev(&b_st, A, &b_i, dt_data, &j, V);
          i = D->size[0] * D->size[1];
          D->size[0] = A->size[0];
          D->size[1] = A->size[0];
          emxEnsureCapacity_creal32_T(&st, D, i, &bf_emlrtRTEI);
          D_data = D->data;
          j = A->size[0] * A->size[0];
          for (i = 0; i < j; i++) {
            D_data[i].re = 0.0F;
            D_data[i].im = 0.0F;
          }
          b_st.site = &ii_emlrtRSI;
          for (j = 0; j < n; j++) {
            D_data[j + D->size[0] * j] = dt_data[j];
          }
          if ((b_i != 0) && (!emlrtSetWarningFlag(&st))) {
            b_st.site = &hi_emlrtRSI;
            b_warning(&b_st);
          }
        }
      }
    }
  }
  emlrtHeapReferenceStackLeaveFcnR2012b((emlrtConstCTX)sp);
}

/* End of code generation (eig.c) */
