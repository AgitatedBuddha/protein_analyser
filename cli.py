"""
CLI for Nutrition Label Extraction

Commands:
    nutrients   - Extract nutrition profile
    aminoacids  - Extract amino acid profile
    all         - Extract both profiles
"""

import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from extractors import (
    NutritionExtractor,
    AminoacidExtractor,
    ExtractionResult,
    BrandExtractionResult,
    extract_brand,
    detect_profile_type,
    get_brand_from_path,
    EXTRACTORS,
)

console = Console()

# Default output directory
DEFAULT_OUTPUT_DIR = Path("output")


def ensure_output_dir(brand_name: str) -> Path:
    """Create and return output directory for a brand."""
    output_dir = DEFAULT_OUTPUT_DIR / brand_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def display_result(result: ExtractionResult, verbose: bool = False):
    """Display extraction result in a formatted table."""
    status_color = "green" if result.valid else "red"
    status_text = "✓ Valid" if result.valid else "✗ Invalid"
    
    console.print(Panel(
        f"[bold {status_color}]{status_text}[/] | Provider: [cyan]{result.provider}[/] | "
        f"Model: [cyan]{result.model}[/] | "
        f"Confidence: [yellow]{result.quality.get('extraction_confidence', 'N/A')}[/]",
        title=f"[{result.profile_type}] {result.product_id}",
        border_style=status_color,
    ))
    
    # Extracted fields table
    table = Table(title="Extracted Fields", show_header=True)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    
    def add_fields(fields: dict, prefix: str = ""):
        for field, value in fields.items():
            if isinstance(value, dict):
                add_fields(value, f"{prefix}{field}.")
            else:
                display_value = str(value) if value is not None else "[dim]null[/]"
                table.add_row(f"{prefix}{field}", display_value)
    
    add_fields(result.extracted_fields)
    console.print(table)
    
    # Show warnings if any
    if result.quality.get("warnings"):
        console.print("\n[yellow]⚠ Warnings:[/]")
        for warning in result.quality["warnings"]:
            console.print(f"  • {warning}")
    
    # Show validation errors if any
    if result.validation_errors:
        console.print("\n[red]✗ Validation Errors:[/]")
        for error in result.validation_errors:
            console.print(f"  • {error}")
    
    # Verbose: show raw evidence
    if verbose:
        console.print("\n[dim]Raw Evidence:[/]")
        console.print_json(json.dumps(result.raw_evidence, indent=2))


def display_brand_result(result: BrandExtractionResult):
    """Display brand extraction result."""
    console.print(Panel(
        f"[bold green]{result.brand}[/] | {result.extraction_timestamp}",
        title="Brand Extraction Complete",
        border_style="green",
    ))
    
    # Nutrients summary
    if result.nutrients:
        nutrients = result.nutrients.get("extracted_fields", {})
        valid = result.nutrients.get("valid", False)
        status = "[green]✓[/]" if valid else "[red]✗[/]"
        console.print(f"\n{status} [cyan]Nutrients:[/]")
        console.print(f"  Serving: {nutrients.get('serving_size_g', 'N/A')}g")
        console.print(f"  Protein: {nutrients.get('protein_g_per_serving', 'N/A')}g")
        console.print(f"  Energy: {nutrients.get('energy_kcal_per_serving', 'N/A')} kcal")
    else:
        console.print("\n[dim]Nutrients: Not found/extracted[/]")
    
    # Amino acids summary
    if result.aminoacids:
        amino = result.aminoacids.get("extracted_fields", {})
        valid = result.aminoacids.get("valid", False)
        status = "[green]✓[/]" if valid else "[red]✗[/]"
        console.print(f"\n{status} [cyan]Amino Acids:[/]")
        eaas = amino.get("eaas", {})
        bcaas = eaas.get("bcaas", {})
        console.print(f"  EAAs: {eaas.get('total_g', 'N/A')}g")
        console.print(f"  BCAAs: {bcaas.get('total_g', 'N/A')}g")
    else:
        console.print("\n[dim]Amino Acids: Not found/extracted[/]")


def resolve_image_path(path: Path, extractor_class) -> Path:
    """Resolve path to image: if directory, find the appropriate image."""
    if path.is_file():
        return path
    elif path.is_dir():
        img = extractor_class.find_image(path)
        if img:
            return img
        raise click.ClickException(f"No {extractor_class.PROFILE_TYPE} image found in {path}")
    else:
        raise click.ClickException(f"Path does not exist: {path}")


@click.group()
def cli():
    """Analyse - Nutrition Label Extraction CLI
    
    Extract nutrition and amino acid information from protein powder labels.
    
    \b
    Commands:
      nutrients   Extract nutrition profile
      aminoacids  Extract amino acid profile
      all         Extract both profiles
    """
    pass


# ============================================================================
# NUTRIENTS - Extract nutrition profile
# ============================================================================

@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--provider", "-P", type=click.Choice(["openai", "gemini"]), default="gemini", help="LLM provider")
@click.option("--model", "-m", default=None, help="Model override")
@click.option("--output", "-o", type=click.Path(), default=None, help="Custom output path")
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
def nutrients(path: str, provider: str, model: Optional[str], output: Optional[str], verbose: bool):
    """Extract nutrition profile from an image or brand directory.
    
    Output saved to: output/<brand>/nutrients.json
    """
    path = Path(path)
    
    try:
        image_path = resolve_image_path(path, NutritionExtractor)
        brand = get_brand_from_path(image_path)
        product_id = f"{brand}_nutrients"
        
        console.print(f"\n[bold]Extracting nutrients from:[/] {image_path}")
        console.print(f"[dim]Provider: {provider} | Model: {model or 'default'}[/]\n")
        
        extractor = NutritionExtractor(provider=provider, model=model)
        
        with console.status("[bold green]Extracting..."):
            result = extractor.extract(image_path, product_id)
        
        display_result(result, verbose)
        
        # Save to structured output path
        if output:
            output_path = Path(output)
        else:
            output_dir = ensure_output_dir(brand)
            output_path = output_dir / "nutrients.json"
        
        with open(output_path, "w") as f:
            json.dump(result.model_dump(), f, indent=2)
        console.print(f"\n[green]✓ Saved to {output_path}[/]")
        
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/]")
        raise click.Abort()


# ============================================================================
# AMINOACIDS - Extract amino acid profile
# ============================================================================

@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--provider", "-P", type=click.Choice(["openai", "gemini"]), default="gemini", help="LLM provider")
@click.option("--model", "-m", default=None, help="Model override")
@click.option("--output", "-o", type=click.Path(), default=None, help="Custom output path")
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
def aminoacids(path: str, provider: str, model: Optional[str], output: Optional[str], verbose: bool):
    """Extract amino acid profile from an image or brand directory.
    
    Output saved to: output/<brand>/aminoacids.json
    """
    path = Path(path)
    
    try:
        image_path = resolve_image_path(path, AminoacidExtractor)
        brand = get_brand_from_path(image_path)
        product_id = f"{brand}_aminoacid"
        
        console.print(f"\n[bold]Extracting amino acids from:[/] {image_path}")
        console.print(f"[dim]Provider: {provider} | Model: {model or 'default'}[/]\n")
        
        extractor = AminoacidExtractor(provider=provider, model=model)
        
        with console.status("[bold green]Extracting..."):
            result = extractor.extract(image_path, product_id)
        
        display_result(result, verbose)
        
        # Save to structured output path
        if output:
            output_path = Path(output)
        else:
            output_dir = ensure_output_dir(brand)
            output_path = output_dir / "aminoacids.json"
        
        with open(output_path, "w") as f:
            json.dump(result.model_dump(), f, indent=2)
        console.print(f"\n[green]✓ Saved to {output_path}[/]")
        
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/]")
        raise click.Abort()


# ============================================================================
# ALL - Extract both profiles from a brand directory
# ============================================================================

@cli.command()
@click.argument("brand_dir", type=click.Path(exists=True))
@click.option("--provider", "-P", type=click.Choice(["openai", "gemini"]), default="gemini", help="LLM provider")
@click.option("--model", "-m", default=None, help="Model override")
@click.option("--output", "-o", type=click.Path(), default=None, help="Custom output path")
@click.option("--weight", "-w", type=float, default=None, help="Product weight in kg")
@click.option("--price", "-p", type=float, default=None, help="Product price in INR")
def all(brand_dir: str, provider: str, model: Optional[str], output: Optional[str], weight: Optional[float], price: Optional[float]):
    """Extract both nutrition and amino acid profiles from a brand directory.
    
    Optionally include --weight (kg) and --price (INR) for value calculations.
    
    Output saved to: output/<brand>/<brand>.json
    """
    from extractors import ProductInfo
    
    brand_dir = Path(brand_dir)
    brand_name = brand_dir.name
    
    console.print(f"\n[bold]Extracting all profiles for:[/] {brand_name}")
    console.print(f"[dim]Provider: {provider} | Model: {model or 'default'}[/]\n")
    
    try:
        with console.status(f"[bold green]Extracting profiles for {brand_name}..."):
            result = extract_brand(brand_dir, provider=provider, model=model)
        
        # Add product info if weight/price provided
        if weight is not None or price is not None:
            product_info = {"weight_kg": weight, "price_inr": price}
            
            # Compute derived values
            if weight and price:
                product_info["price_per_kg"] = round(price / weight, 2)
            
            # Compute servings per pack and price per serving
            if weight and result.nutrients:
                serving_size_g = result.nutrients.get("extracted_fields", {}).get("serving_size_g")
                if serving_size_g:
                    servings_per_pack = (weight * 1000) / serving_size_g
                    product_info["servings_per_pack"] = round(servings_per_pack, 1)
                    
                    if price:
                        product_info["price_per_serving"] = round(price / servings_per_pack, 2)
            
            result.product_info = ProductInfo(**product_info)
        
        display_brand_result(result)
        
        # Display product info if available
        if result.product_info:
            console.print(f"\n[cyan]Product Info:[/]")
            if result.product_info.weight_kg:
                console.print(f"  Weight: {result.product_info.weight_kg} kg")
            if result.product_info.price_inr:
                console.print(f"  Price: ₹{result.product_info.price_inr}")
            if result.product_info.price_per_kg:
                console.print(f"  Price per kg: ₹{result.product_info.price_per_kg}")
            if result.product_info.servings_per_pack:
                console.print(f"  Servings per pack: {result.product_info.servings_per_pack}")
            if result.product_info.price_per_serving:
                console.print(f"  Price per serving: ₹{result.product_info.price_per_serving}")
        
        # Save to structured output path
        if output:
            output_path = Path(output)
        else:
            output_dir = ensure_output_dir(brand_name)
            output_path = output_dir / f"{brand_name}.json"
        
        with open(output_path, "w") as f:
            json.dump(result.model_dump(), f, indent=2)
        console.print(f"\n[green]✓ Saved to {output_path}[/]")
        
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/]")
        raise click.Abort()


# ============================================================================
# UTILITY COMMANDS
# ============================================================================

@cli.command()
@click.option("--provider", "-P", type=click.Choice(["openai", "gemini"]), default="gemini")
def check(provider: str):
    """Check if API credentials are configured."""
    import os
    
    key_name = "OPENAI_API_KEY" if provider == "openai" else "GOOGLE_API_KEY"
    key = os.getenv(key_name)
    
    if key:
        masked = key[:8] + "..." + key[-4:]
        console.print(f"[green]✓ {key_name}:[/] {masked}")
    else:
        console.print(f"[red]✗ {key_name} not set[/]")
        console.print(f"[dim]export {key_name}=your_api_key[/]")


@cli.command()
def skills():
    """List available extraction skills."""
    console.print("\n[bold]Available Extractors:[/]\n")
    
    table = Table(show_header=True)
    table.add_column("Command", style="cyan")
    table.add_column("Extractor", style="green")
    table.add_column("Skill Files", style="dim")
    
    for profile_type, extractor_cls in EXTRACTORS.items():
        table.add_row(
            profile_type,
            extractor_cls.__name__,
            f"{extractor_cls.PROMPT_FILE}, {extractor_cls.SCHEMA_FILE}",
        )
    
    console.print(table)


# ============================================================================
# SCORING COMMANDS
# ============================================================================

# Mode explanations derived from scoring_spec.yml
MODE_EXPLANATIONS = {
    "cut": """[bold cyan]CUT Mode[/] - Optimized for cutting/weight loss
  [dim]Weights:[/] Protein per 100kcal (40%) + Leucine (30%) + Protein% (20%) + EAAs% (10%)
  [dim]Penalties:[/] High sodium (-10%), High non-protein macros (-15%)
  [dim]Hard reject:[/] Protein <18g per 100kcal, Leucine <2.2g per serving""",
    
    "bulk": """[bold cyan]BULK Mode[/] - Optimized for muscle building
  [dim]Weights:[/] Protein% (35%) + EAAs% (30%) + Leucine (25%) + Protein/serving (10%)
  [dim]Penalties:[/] High sodium (-5%), High non-protein macros (-5%)
  [dim]No hard rejections[/] - all brands considered""",
    
    "clean": """[bold cyan]CLEAN Mode[/] - Optimized for clean ingredients
  [dim]Weights:[/] Low sodium (35%) + Low non-protein macros (30%) + EAAs% (15%) + Leucine (10%) + Protein% (10%)
  [dim]Hard reject:[/] Sodium >250mg, Added sugar present, Amino spiking suspected"""
}


def display_mode_explanation(mode: Optional[str] = None):
    """Display explanation of scoring logic for a mode."""
    if mode:
        console.print(f"\n{MODE_EXPLANATIONS[mode]}\n")
    else:
        for m, explanation in MODE_EXPLANATIONS.items():
            console.print(f"\n{explanation}")
        console.print("")


@cli.command()
@click.argument("brand", required=False)
@click.option("--mode", "-m", type=click.Choice(["cut", "bulk", "clean"]), default=None, help="Score for specific mode only")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed component scores")
@click.option("--no-explain", is_flag=True, help="Hide scoring logic explanation")
def score(brand: Optional[str], mode: Optional[str], verbose: bool, no_explain: bool):
    """Score brands based on scoring_spec.yml.
    
    \b
    Examples:
      analyse score                    # Score all brands with explanation
      analyse score muscle_blaze       # Score specific brand
      analyse score --mode cut         # Score all for cutting
      analyse score --no-explain       # Hide explanation
    """
    from scorer import Scorer, score_all_brands
    
    # Show explanation by default
    if not no_explain:
        display_mode_explanation(mode)
    
    scorer = Scorer()
    
    if brand:
        # Score specific brand
        json_path = DEFAULT_OUTPUT_DIR / brand / f"{brand}.json"
        if not json_path.exists():
            console.print(f"[red]✗ Brand not found: {json_path}[/]")
            raise click.Abort()
        
        scores = scorer.score_brand_from_file(json_path)
        display_brand_scores(scores, mode, verbose)
    else:
        # Score all brands
        results = score_all_brands(DEFAULT_OUTPUT_DIR)
        console.print(f"\n[bold]Scoring {len(results)} brands[/]\n")
        
        for scores in results:
            display_brand_scores(scores, mode, verbose)
            console.print("")



def display_brand_scores(scores, mode: Optional[str], verbose: bool):
    """Display scores for a brand."""
    from scorer import BrandScores
    
    modes_to_show = [mode] if mode else ["cut", "bulk", "clean"]
    
    # Header with brand name and spiking status
    spiking_status = "[red]⚠ SPIKING SUSPECTED[/]" if scores.amino_spiking.suspected else ""
    console.print(Panel(
        f"[bold]{scores.brand}[/] {spiking_status}",
        border_style="cyan"
    ))
    
    # Show metrics summary
    m = scores.metrics
    console.print(f"  Protein: [green]{m.protein_pct:.1f}%[/] | "
                  f"Per 100kcal: [green]{m.protein_per_100_kcal:.1f}g[/] | "
                  f"Leucine: [green]{m.leucine_g_per_serving or 'N/A'}g[/]")
    
    if m.eaas_pct:
        console.print(f"  EAAs: [yellow]{m.eaas_pct*100:.1f}%[/] of protein | "
                      f"Non-protein macros: [yellow]{m.non_protein_macros_g:.1f}g[/] | "
                      f"Sodium: [yellow]{m.sodium_mg}mg[/]")
    
    # Show amino spiking rules triggered
    if scores.amino_spiking.triggered_rules:
        console.print(f"  [dim]Spiking rules: {', '.join(scores.amino_spiking.triggered_rules)}[/]")
    
    # Show mode scores
    table = Table(show_header=True)
    table.add_column("Mode", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Status")
    
    for m_name in modes_to_show:
        mode_score = getattr(scores, f"{m_name}_score")
        if mode_score:
            if mode_score.hard_rejected:
                score_str = "[red]REJECTED[/]"
                status = f"[red]{mode_score.rejection_reason}[/]"
            else:
                score_val = mode_score.total_score
                if score_val >= 0.7:
                    score_str = f"[green]{score_val:.2f}[/]"
                elif score_val >= 0.5:
                    score_str = f"[yellow]{score_val:.2f}[/]"
                else:
                    score_str = f"[red]{score_val:.2f}[/]"
                status = f"[dim]penalty: -{mode_score.penalty_deduction:.2f}[/]" if mode_score.penalty_deduction else ""
            
            table.add_row(m_name.upper(), score_str, status)
    
    console.print(table)
    
    # Verbose: show component scores
    if verbose:
        for m_name in modes_to_show:
            mode_score = getattr(scores, f"{m_name}_score")
            if mode_score and mode_score.component_scores:
                console.print(f"\n[dim]{m_name.upper()} components:[/]")
                for comp, data in mode_score.component_scores.items():
                    if "contribution" in data:
                        console.print(f"  {comp}: {data['raw_value']} → {data['normalized']:.2f} × {data['weight']} = {data['contribution']:.3f}")
                    elif "deduction" in data:
                        console.print(f"  {comp}: {data['raw_value']} → penalty {data['penalty']:.2f} × {data['weight']} = -{data['deduction']:.3f}")


@cli.command()
@click.option("--mode", "-m", type=click.Choice(["cut", "bulk", "clean"]), default="cut", help="Mode to rank by")
def leaderboard(mode: str):
    """Show ranked leaderboard of all brands for a mode.
    
    \b
    Examples:
      analyse leaderboard              # Leaderboard for cutting (default)
      analyse leaderboard --mode bulk  # Leaderboard for bulking
    """
    from scorer import score_all_brands, get_leaderboard
    
    results = score_all_brands(DEFAULT_OUTPUT_DIR)
    rankings = get_leaderboard(results, mode)
    
    console.print(f"\n[bold]🏆 Leaderboard: {mode.upper()} Mode[/]\n")
    
    table = Table(show_header=True)
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Brand")
    table.add_column("Score", justify="right")
    table.add_column("Status")
    
    for i, (brand, score_val, rejected) in enumerate(rankings, 1):
        if rejected:
            rank = "[dim]-[/]"
            score_str = "[red]REJECTED[/]"
            status = "[dim]Hard reject[/]"
        else:
            rank = f"[bold]{i}[/]" if i <= 3 else str(i)
            if score_val >= 0.7:
                score_str = f"[green]{score_val:.3f}[/]"
            elif score_val >= 0.5:
                score_str = f"[yellow]{score_val:.3f}[/]"
            else:
                score_str = f"[red]{score_val:.3f}[/]"
            
            if i == 1:
                status = "[green]🥇 Best[/]"
            elif i == 2:
                status = "[yellow]🥈[/]"
            elif i == 3:
                status = "[yellow]🥉[/]"
            else:
                status = ""
        
        table.add_row(rank, brand, score_str, status)
    
    console.print(table)


# Entry point
def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
