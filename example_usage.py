"""
Example usage of the Chrono24 data analysis module.

This script demonstrates how to use the json_processing module to analyze
Chrono24 watch listings data.
"""

from json_processing import Chrono24Analyzer, get_price_summary, get_total_price_summary


def main():
    """Main function demonstrating various analysis features."""

    # Path to the JSON data file
    json_path = "json_results/all_listings.json"

    try:
        print("=== CHRONO24 DATA ANALYSIS EXAMPLE ===\n")

        # Method 1: Using convenience functions for quick analysis
        print("1. QUICK ANALYSIS USING CONVENIENCE FUNCTIONS")
        print("-" * 50)

        price_stats = get_price_summary(json_path)
        print(f"Average watch price: ${price_stats['average']:,.2f}")
        print(f"Price standard deviation: ${price_stats['std_dev']:,.2f}")
        print(f"Price range: ${price_stats['min']:,.2f} - ${price_stats['max']:,.2f}")

        total_stats = get_total_price_summary(json_path)
        print(f"Average total cost (with shipping): ${total_stats['average']:,.2f}")
        print(f"Total cost standard deviation: ${total_stats['std_dev']:,.2f}")

        # Method 2: Using the full analyzer for comprehensive analysis
        print("\n\n2. COMPREHENSIVE ANALYSIS USING ANALYZER CLASS")
        print("-" * 55)

        analyzer = Chrono24Analyzer(json_path)

        # Price analysis
        print("\nPRICE ANALYSIS:")
        price_data = analyzer.get_price_statistics()
        print(f"  • Count: {price_data['count']} watches")
        print(f"  • Average: ${price_data['average']:,.2f}")
        print(f"  • Median: ${price_data['median']:,.2f}")
        print(f"  • Standard Deviation: ${price_data['std_dev']:,.2f}")
        print(f"  • Range: ${price_data['min']:,.2f} - ${price_data['max']:,.2f}")

        # Shipping analysis
        shipping_data = analyzer.get_shipping_statistics()
        print(f"\nSHIPPING ANALYSIS:")
        print(f"  • Average shipping: ${shipping_data['average']:,.2f}")
        print(f"  • Shipping std dev: ${shipping_data['std_dev']:,.2f}")
        print(
            f"  • Shipping range: ${shipping_data['min']:,.2f} - ${shipping_data['max']:,.2f}"
        )

        # Location analysis
        print(f"\nLOCATION ANALYSIS:")
        location_stats = analyzer.get_location_statistics()
        print("  Top locations by number of listings:")

        # Sort locations by count
        sorted_locations = sorted(
            location_stats.items(), key=lambda x: x[1]["count"], reverse=True
        )

        for i, (location, stats) in enumerate(sorted_locations[:5]):
            print(f"  {i+1}. {location}: {stats['count']} listings")
            print(
                f"     Avg price: ${stats['avg_price']:,.2f} (±${stats['price_std_dev']:,.2f})"
            )

        # Merchant analysis
        print(f"\nMERCHANT ANALYSIS:")
        merchant_stats = analyzer.get_merchant_statistics()
        for merchant, stats in merchant_stats.items():
            print(f"  • {merchant}: {stats['count']} listings")
            print(
                f"    Avg price: ${stats['avg_price']:,.2f} (±${stats['price_std_dev']:,.2f})"
            )
            print(f"    Avg shipping: ${stats['avg_shipping']:,.2f}")

        # Summary insights
        print(f"\n\n3. KEY INSIGHTS")
        print("-" * 20)

        dealer_count = merchant_stats.get("Dealer", {}).get("count", 0)
        private_count = merchant_stats.get("Private Seller", {}).get("count", 0)
        total_listings = dealer_count + private_count

        print(f"• Total listings analyzed: {total_listings}")
        print(
            f"• {dealer_count/total_listings*100:.1f}% from dealers, {private_count/total_listings*100:.1f}% from private sellers"
        )
        print(
            f"• Dealers charge average ${merchant_stats.get('Dealer', {}).get('avg_shipping', 0):,.2f} shipping"
        )
        print(
            f"• Private sellers charge average ${merchant_stats.get('Private Seller', {}).get('avg_shipping', 0):,.2f} shipping"
        )

        # Only calculate if we have numeric data (not error messages)
        if isinstance(price_data["std_dev"], (int, float)) and isinstance(
            price_data["average"], (int, float)
        ):
            price_cv = (price_data["std_dev"] / price_data["average"]) * 100
            print(
                f"• Price coefficient of variation: {price_cv:.1f}% (shows price diversity)"
            )

        if (
            isinstance(total_stats["average"], (int, float))
            and isinstance(price_data["average"], (int, float))
            and total_stats["average"] > price_data["average"]
        ):
            shipping_impact = total_stats["average"] - price_data["average"]
            print(
                f"• Shipping adds average ${shipping_impact:,.2f} ({shipping_impact/price_data['average']*100:.1f}%) to total cost"
            )

    except FileNotFoundError:
        print(f"Error: Could not find the JSON file at {json_path}")
        print("Make sure the file exists and the path is correct.")
    except Exception as e:
        print(f"Error during analysis: {e}")


if __name__ == "__main__":
    main()
