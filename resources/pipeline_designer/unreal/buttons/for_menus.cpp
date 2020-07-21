#include "Extender.h"
#include <vector>
#include "Json.h"
#include "ExtenderCommands.h"
#include "LevelEditor.h"
#include <fstream>
#include <iostream>
#define LOCTEXT_NAMESPACE "FExtenderModule"

void FExtenderModule::AddMenuButton(FMenuBuilder& MenuBuilder)
{
	MenuBuilder.BeginSection("SectionName");
	{
		MenuBuilder.AddMenuEntry(
			// this arguent should be CapitalCase of the button name so this would be "Open"
			FText::FromString("ButtonName"),
			// this argument would be a variable that we get from the json file.
			FText::FromString("Button Tool Tip"),
			FSlateIcon(),
			FUIAction(FExecuteAction::CreateRaw(this, &FExtenderModule::Run))
		);
	}
	MenuBuilder.EndSection();
}

void FExtenderModule::Run()
{
	UE_LOG(LogTemp, Warning, TEXT("ButtonName: Hello World!"));
}
#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FExtenderModule, Extender)