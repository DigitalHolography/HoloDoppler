/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * sortLE.c
 *
 * Code generation for function 'sortLE'
 *
 */

/* Include files */
#include "sortLE.h"
#include "rt_nonfinite.h"
#include "mwmathutil.h"
#include <string.h>

/* Function Definitions */
boolean_T sortLE(const creal32_T v_data[], int32_T idx1, int32_T idx2)
{
  boolean_T p;
  if (muSingleScalarIsNaN(v_data[idx2 - 1].re) ||
      muSingleScalarIsNaN(v_data[idx2 - 1].im)) {
    p = (muSingleScalarIsNaN(v_data[idx1 - 1].re) ||
         muSingleScalarIsNaN(v_data[idx1 - 1].im));
  } else if (muSingleScalarIsNaN(v_data[idx1 - 1].re) ||
             muSingleScalarIsNaN(v_data[idx1 - 1].im)) {
    p = true;
  } else {
    real32_T bi;
    real32_T x;
    boolean_T SCALEA;
    boolean_T SCALEB;
    if ((muSingleScalarAbs(v_data[idx1 - 1].re) > 1.70141173E+38F) ||
        (muSingleScalarAbs(v_data[idx1 - 1].im) > 1.70141173E+38F)) {
      SCALEA = true;
    } else {
      SCALEA = false;
    }
    if ((muSingleScalarAbs(v_data[idx2 - 1].re) > 1.70141173E+38F) ||
        (muSingleScalarAbs(v_data[idx2 - 1].im) > 1.70141173E+38F)) {
      SCALEB = true;
    } else {
      SCALEB = false;
    }
    if (SCALEA || SCALEB) {
      x = muSingleScalarHypot(v_data[idx1 - 1].re / 2.0F,
                              v_data[idx1 - 1].im / 2.0F);
      bi = muSingleScalarHypot(v_data[idx2 - 1].re / 2.0F,
                               v_data[idx2 - 1].im / 2.0F);
    } else {
      x = muSingleScalarHypot(v_data[idx1 - 1].re, v_data[idx1 - 1].im);
      bi = muSingleScalarHypot(v_data[idx2 - 1].re, v_data[idx2 - 1].im);
    }
    if (x == bi) {
      x = muSingleScalarAtan2(v_data[idx1 - 1].im, v_data[idx1 - 1].re);
      bi = muSingleScalarAtan2(v_data[idx2 - 1].im, v_data[idx2 - 1].re);
      if (x == bi) {
        real32_T ai;
        real32_T ar;
        real32_T br;
        ar = v_data[idx1 - 1].re;
        ai = v_data[idx1 - 1].im;
        br = v_data[idx2 - 1].re;
        bi = v_data[idx2 - 1].im;
        if (ar != br) {
          if (x >= 0.0F) {
            x = br;
            bi = ar;
          } else {
            x = ar;
            bi = br;
          }
        } else if (ar < 0.0F) {
          x = bi;
          bi = ai;
        } else {
          x = ai;
        }
        if (x == bi) {
          x = 0.0F;
          bi = 0.0F;
        }
      }
    }
    p = (x >= bi);
  }
  return p;
}

/* End of code generation (sortLE.c) */
