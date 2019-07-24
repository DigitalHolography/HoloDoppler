#pragma once
#include "DemoHead.h"
#include "Cine.h"

//abstract class
class ISource
{
public:
	virtual Cine* CurrentCine() = 0;

};
