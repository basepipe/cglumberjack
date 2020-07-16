#pragma once
#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
class FCustomMenu : public IModuleInterface
{
public:
	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
	// load all menus from .json file
	// void LoadMenus();
	// register an individual menu
	void RegisterMenu(String PreviousMenu="Help");
	//Functions called by Extension object to fill extension with menus/toolbars
	void AddMenu(FMenuBarBuilder& MenuBuilder,
                              String MenuName="MenuName",
                              String MenuToolTip="Menu Tool Tip");
	//Functions that add the menu entries to the specific menu/submenu object
	void AddButton(FMenuBuilder& MenuBuilder,
                    String SectionName="SectionName",
                    String ButtonName="ButtonName",
                    String ButtonToolTip="ButtonToolTip",
                    );
	//Functions mapped to specific buttons to print to LOG when clicked
	void Run();
};