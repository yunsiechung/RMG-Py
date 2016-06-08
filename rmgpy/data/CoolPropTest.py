import CoolProp as CP

from CoolProp.CoolProp import PropsSI


print PropsSI('D','T',600,'Q',0,'Water') #saturation density of water in liquid phase (0 means liquid) at 600K
print PropsSI('T','D',649.411406204,'Q',0,'Water') #get the saturation temperature of water at the density of 649.31 kg/m^3

