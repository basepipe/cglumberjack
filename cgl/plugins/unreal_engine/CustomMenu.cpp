#include "CustomMenu.h"
#include <vector>
#include "Json.h"
#include "ExtenderCommands.h"
#include "LevelEditor.h"
#include <fstream>
#include <iostream>


void FCustomMenu::RegisterMenu(String PreviousMenu="Help")
{
	TSharedPtr<FExtender> Extend = MakeShareable(new FExtender);
	Extend->AddMenuBarExtension(PreviousMenu,
	                            EExtensionHook::After,
	                            NULL,
	                            FMenuBarExtensionDelegate::CreateRaw(this, &FCustomMenu::AddMenu)
	                            );
	FLevelEditorModule& LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");
	LevelEditorModule.GetMenuExtensibilityManager()->AddExtender(Extend);
}

void FCustomMenu::AddMenu(FMenuBarBuilder& MenuBuilder,
                              String MenuName="MenuName",
                              String MenuToolTip="Menu Tool Tip")
{
	MenuBuilder.AddPullDownMenu(
		FText::FromString(MenuName),
		FText::FromString(MenuToolTip),
		// ADD BUTTONS
		// this is the code to do that.
		// FNewMenuDelegate::CreateRaw(this, &FCustomMenu::AddMenuButton), "MenuName"
	);
}

// we need a "add menu buttons

void FCustomMenu::AddButton(FMenuBuilder& MenuBuilder,
                                String SectionName="SectionName",
                                String ButtonName="ButtonName",
                                String ButtonToolTip="ButtonToolTip",
                                )
{
	MenuBuilder.BeginSection(SectionName);
	{
		MenuBuilder.AddMenuEntry(
			// this arguent should be CapitalCase of the button name so this would be "Open"
			FText::FromString(ButtonName),
			// this argument would be a variable that we get from the json file.
			FText::FromString(ButtonToolTip),
			FSlateIcon(),
			// This "Run" needs to point to a seperate file.
			FUIAction(FExecuteAction::CreateRaw(this, &FCustomMenu::Run))
		);
	}
	MenuBuilder.EndSection();
}

void FCustomMenu::Run()
{
	UE_LOG(LogTemp, Warning, TEXT("Hello World!"));
}
#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FCustomMenu, CustomMenu)